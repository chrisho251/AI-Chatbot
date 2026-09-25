"""Corpus versions. Build a candidate, publish it, reject it, or roll serving back.

Version numbers only grow. Publishing version N compares it with the latest published version L,
opens validity intervals for chunks that are new in N and closes those that N dropped. Readers
pinned to L never see these changes, because every new interval starts at N and N is above L.
If publish stops halfway it can simply run again, every step is safe to repeat.
Rollback only moves the serving alias. The intervals already describe every older version.
"""

from collections.abc import Collection, Sequence

from chatbot_contracts.corpus import ChunkSet, CorpusManifest
from chatbot_contracts.enums import CorpusStatus
from chatbot_platform.errors import VersioningError
from chatbot_platform.index import ServingIndex
from chatbot_platform.models import CANDIDATE_ALIAS, SERVING_ALIAS
from chatbot_platform.registry import Registry


def create_candidate(
    registry: Registry,
    *,
    add: Collection[str] = (),
    remove: Collection[str] = (),
    embedding_model: str,
    chunker_version: str,
) -> CorpusManifest:
    """New candidate from the serving version, plus added and minus removed document versions.

    Versions superseded by an added version and retracted versions are removed automatically.
    """
    unknown = set(add) - set(registry.doc_versions_by_id(add))
    if unknown:
        raise VersioningError(f"unknown document versions {sorted(unknown)}")
    parent_id = registry.get_alias(SERVING_ALIAS)
    base = set(registry.get_corpus_version(parent_id).doc_versions) if parent_id else set()
    added = registry.doc_versions_by_id(add)
    superseded = {doc.supersedes for doc in added.values() if doc.supersedes}
    dropped = set(remove) | superseded | registry.retracted(base | set(add))
    manifest = CorpusManifest(
        producer="platform",
        version_id=registry.next_version_id(),
        parent_version=parent_id,
        doc_versions=sorted((base | set(add)) - dropped),
        embedding_model=embedding_model,
        chunker_version=chunker_version,
        status=CorpusStatus.CANDIDATE,
    )
    registry.add_corpus_version(manifest)
    registry.set_alias(CANDIDATE_ALIAS, manifest.version_id)
    return manifest


def publish(
    registry: Registry,
    index: ServingIndex,
    version_id: int,
    chunk_sets: Sequence[ChunkSet],
) -> CorpusManifest:
    """Publish an approved candidate and move the serving alias to it.

    chunk_sets holds the new chunks of this candidate. Chunks of unchanged documents are reused
    from the latest published version when the embedding model and chunker did not change.
    """
    manifest = registry.get_corpus_version(version_id)
    if manifest.status == CorpusStatus.PUBLISHED:
        return manifest
    _require_publishable(registry, manifest)
    _require_matching_sets(manifest, chunk_sets)

    latest = registry.latest_published()
    active = index.active_chunks(latest.version_id) if latest else {}
    reusable = _reusable_chunks(registry, index, manifest, latest)
    rebuilt = {chunk_set.doc_version for chunk_set in chunk_sets}
    wanted_docs = set(manifest.doc_versions)
    retained = {
        chunk_id
        for chunk_id, doc_version in reusable.items()
        if doc_version in wanted_docs and doc_version not in rebuilt
    }
    new_ids = {chunk.chunk_id for chunk_set in chunk_sets for chunk in chunk_set.chunks}
    covered = {reusable[chunk_id] for chunk_id in retained} | rebuilt
    missing = wanted_docs - covered
    if missing:
        raise VersioningError(f"no chunks for document versions {sorted(missing)}")

    target = retained | new_ids
    for chunk_set in chunk_sets:
        index.add_chunk_set(chunk_set)
    index.close_intervals(set(active) - target, version_id)
    index.open_intervals(target - set(active), version_id)
    registry.set_alias(SERVING_ALIAS, version_id)
    registry.set_corpus_status(version_id, CorpusStatus.PUBLISHED)
    return registry.get_corpus_version(version_id)


def reject(registry: Registry, version_id: int) -> None:
    manifest = registry.get_corpus_version(version_id)
    if manifest.status != CorpusStatus.CANDIDATE:
        raise VersioningError(f"version {version_id} is {manifest.status}, not a candidate")
    registry.set_corpus_status(version_id, CorpusStatus.REJECTED)


def rollback(registry: Registry, version_id: int) -> None:
    """Point serving at an older published version."""
    manifest = registry.get_corpus_version(version_id)
    if manifest.status != CorpusStatus.PUBLISHED:
        raise VersioningError(f"version {version_id} was never published")
    registry.set_alias(SERVING_ALIAS, version_id)


def _reusable_chunks(
    registry: Registry,
    index: ServingIndex,
    manifest: CorpusManifest,
    latest: CorpusManifest | None,
) -> dict[str, str]:
    """Chunks of the latest published version and of the candidate parent, when encoded alike.

    The parent matters after a rollback, when it holds chunks the latest version already dropped.
    """
    parent = (
        registry.get_corpus_version(manifest.parent_version) if manifest.parent_version else None
    )
    encoding = (manifest.embedding_model, manifest.chunker_version)
    reusable: dict[str, str] = {}
    for source in (latest, parent):
        if source and (source.embedding_model, source.chunker_version) == encoding:
            reusable |= index.active_chunks(source.version_id)
    return reusable


def _require_publishable(registry: Registry, manifest: CorpusManifest) -> None:
    if manifest.status != CorpusStatus.CANDIDATE:
        raise VersioningError(f"version {manifest.version_id} is {manifest.status}")
    if manifest.gate_report_id is None:
        raise VersioningError(f"version {manifest.version_id} has no gate report")
    if not registry.get_gate_report(manifest.gate_report_id).approved:
        raise VersioningError(f"version {manifest.version_id} is not approved by the gate")
    latest = registry.latest_published()
    if latest is not None and latest.version_id > manifest.version_id:
        raise VersioningError(
            f"version {manifest.version_id} is older than published version "
            f"{latest.version_id}, build a new candidate"
        )


def _require_matching_sets(manifest: CorpusManifest, chunk_sets: Sequence[ChunkSet]) -> None:
    for chunk_set in chunk_sets:
        if chunk_set.doc_version not in manifest.doc_versions:
            raise VersioningError(f"{chunk_set.doc_version} is not in the candidate")
        if (chunk_set.embedding_model, chunk_set.chunker_version) != (
            manifest.embedding_model,
            manifest.chunker_version,
        ):
            raise VersioningError(f"chunk set for {chunk_set.doc_version} uses another encoder")
