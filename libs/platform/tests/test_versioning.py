import pytest

from chatbot_contracts import samples
from chatbot_contracts.enums import KnowledgeBaseStatus
from chatbot_platform.errors import VersioningError
from chatbot_platform.gate import GateContext, record_sme_decision, run_gate
from chatbot_platform.models import CANDIDATE_ALIAS, SERVING_ALIAS
from chatbot_platform.versioning import create_candidate, publish, reject, rollback

TEXTS = list(samples.PAGE_TEXTS)


def _visible_texts(platform, version):
    active = platform.index.active_chunks(version)
    return sorted(stored.chunk.text for stored in platform.index.get_chunks(active))


def test_first_publish_serves_all_chunks(platform, upload, ingest):
    document = upload(b"edition one")
    manifest = ingest({document.doc_version: TEXTS})
    assert manifest.status == KnowledgeBaseStatus.PUBLISHED
    assert platform.registry.get_alias(SERVING_ALIAS) == manifest.version_id
    assert _visible_texts(platform, manifest.version_id) == sorted(TEXTS)


def test_correction_replaces_old_chunks_and_keeps_other_documents(platform, upload, ingest):
    notes = upload(b"notes", source_id="lecture notes")
    old = upload(b"edition one")
    first = ingest({notes.doc_version: ["Variance measures spread."], old.doc_version: TEXTS})

    new = upload(b"edition two")
    corrected = [*TEXTS[:2], "The standard deviation is the square root of the variance."]
    second = ingest({new.doc_version: corrected})

    assert second.doc_versions == sorted([notes.doc_version, new.doc_version])
    assert _visible_texts(platform, second.version_id) == sorted(
        ["Variance measures spread.", *corrected]
    )
    assert _visible_texts(platform, first.version_id) == sorted(
        ["Variance measures spread.", *TEXTS]
    )


def test_rollback_then_publish_keeps_every_version_correct(platform, upload, ingest):
    old = upload(b"edition one")
    first = ingest({old.doc_version: TEXTS})
    new = upload(b"edition two")
    second = ingest({new.doc_version: ["Only one page now."]})

    rollback(platform.registry, first.version_id)
    notes = upload(b"notes", source_id="lecture notes")
    third = ingest({notes.doc_version: ["Variance measures spread."]})

    assert third.parent_version == first.version_id
    assert _visible_texts(platform, third.version_id) == sorted(
        ["Variance measures spread.", *TEXTS]
    )
    assert _visible_texts(platform, second.version_id) == ["Only one page now."]
    assert _visible_texts(platform, first.version_id) == sorted(TEXTS)


def test_embedding_change_needs_a_full_rebuild(platform, upload, ingest):
    document = upload(b"edition one")
    ingest({document.doc_version: TEXTS})
    refreshed = ingest({document.doc_version: TEXTS}, embedding_model="bge-m3-v2")
    assert refreshed.embedding_model == "bge-m3-v2"
    assert len(platform.index.active_chunks(refreshed.version_id)) == len(TEXTS)


def test_publish_refuses_a_candidate_without_gate_report(platform, upload):
    document = upload(b"edition one")
    manifest = create_candidate(
        platform.registry,
        add=[document.doc_version],
        embedding_model=samples.EMBEDDING_MODEL,
        chunker_version=samples.CHUNKER_VERSION,
    )
    assert platform.registry.get_alias(CANDIDATE_ALIAS) == manifest.version_id
    with pytest.raises(VersioningError, match="no gate report"):
        publish(platform.registry, platform.index, manifest.version_id, [])


def test_publish_refuses_without_sme_approval(platform, upload):
    document = upload(b"edition one")
    manifest = create_candidate(
        platform.registry,
        add=[document.doc_version],
        embedding_model=samples.EMBEDDING_MODEL,
        chunker_version=samples.CHUNKER_VERSION,
    )
    chunk_set = samples.sample_chunk_set(doc_version=document.doc_version)
    pages = [
        samples.sample_clean_page(doc_version=document.doc_version, page_no=p) for p in (1, 2, 3)
    ]
    context = GateContext(manifest, [chunk_set], pages, {document.doc_version: document})
    report = run_gate(platform.registry, context, [])
    assert report.requires_sme and not report.approved
    with pytest.raises(VersioningError, match="not approved"):
        publish(platform.registry, platform.index, manifest.version_id, [chunk_set])


def _approved_candidate(platform, add):
    manifest = create_candidate(
        platform.registry,
        add=add,
        embedding_model=samples.EMBEDDING_MODEL,
        chunker_version=samples.CHUNKER_VERSION,
    )
    report = run_gate(platform.registry, GateContext(manifest, [], [], {}), [])
    record_sme_decision(platform.registry, report.report_id, approved=True, by="sme")
    return manifest


def test_candidate_older_than_serving_cannot_publish(platform, upload, ingest):
    document = upload(b"edition one")
    stale = create_candidate(
        platform.registry,
        add=[document.doc_version],
        embedding_model=samples.EMBEDDING_MODEL,
        chunker_version=samples.CHUNKER_VERSION,
    )
    ingest({document.doc_version: TEXTS})
    report = run_gate(platform.registry, GateContext(stale, [], [], {}), [])
    record_sme_decision(platform.registry, report.report_id, approved=True, by="sme")
    with pytest.raises(VersioningError, match="older than published"):
        publish(platform.registry, platform.index, stale.version_id, [])


def test_publish_refuses_documents_without_chunks(platform, upload, ingest):
    first = upload(b"edition one")
    ingest({first.doc_version: TEXTS})
    other = upload(b"notes", source_id="lecture notes")
    manifest = _approved_candidate(platform, [other.doc_version])
    with pytest.raises(VersioningError, match="no chunks"):
        publish(platform.registry, platform.index, manifest.version_id, [])


def test_retracted_document_leaves_the_next_candidate(platform, upload, ingest):
    keep = upload(b"notes", source_id="lecture notes")
    drop = upload(b"edition one")
    ingest({keep.doc_version: ["Variance measures spread."], drop.doc_version: TEXTS})
    platform.registry.retract(drop.doc_version)
    manifest = create_candidate(
        platform.registry,
        embedding_model=samples.EMBEDDING_MODEL,
        chunker_version=samples.CHUNKER_VERSION,
    )
    assert manifest.doc_versions == [keep.doc_version]


def test_reject_and_rollback_rules(platform, upload, ingest):
    document = upload(b"edition one")
    published = ingest({document.doc_version: TEXTS})
    with pytest.raises(VersioningError):
        reject(platform.registry, published.version_id)
    candidate = create_candidate(
        platform.registry,
        embedding_model=samples.EMBEDDING_MODEL,
        chunker_version=samples.CHUNKER_VERSION,
    )
    reject(platform.registry, candidate.version_id)
    with pytest.raises(VersioningError):
        rollback(platform.registry, candidate.version_id)
