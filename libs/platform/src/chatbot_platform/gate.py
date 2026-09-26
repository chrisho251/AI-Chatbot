"""Quality gate, the only way a candidate knowledge base version reaches serving.

A check is a function from GateContext to CheckResult. default_checks returns the structural checks
built here. The retrieval regression and RAGAs checks belong to the eval lane. Until that lane
passes real ones to run_gate, the placeholders below report skipped, which does not block.
A candidate that adds any new document version also needs an SME decision before publish.
"""

import math
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from chatbot_contracts.base import SCHEMA_VERSION
from chatbot_contracts.enums import KnowledgeBaseStatus, SourceType
from chatbot_contracts.ids import make_chunk_id
from chatbot_contracts.knowledge_base import (
    ChunkSet,
    CleanPage,
    DocumentVersion,
    KnowledgeBaseManifest,
)
from chatbot_platform.errors import VersioningError
from chatbot_platform.models import CheckResult, GateReport, SmeDecision
from chatbot_platform.registry import Registry
from chatbot_platform.settings import PlatformSettings
from chatbot_platform.sql import utcnow


@dataclass(frozen=True)
class GateContext:
    """Everything the checks look at. Pages and chunk sets cover the new document versions only."""

    manifest: KnowledgeBaseManifest
    chunk_sets: Sequence[ChunkSet]
    clean_pages: Sequence[CleanPage]
    documents: Mapping[str, DocumentVersion]


Check = Callable[[GateContext], CheckResult]


def check_schema_versions(ctx: GateContext) -> CheckResult:
    records = [*ctx.chunk_sets, *ctx.clean_pages, *ctx.documents.values()]
    stale = sorted({record.schema_version for record in records} - {SCHEMA_VERSION})
    return _result("schema_versions", [f"unsupported schema version {v}" for v in stale])


def check_chunk_ids(ctx: GateContext) -> CheckResult:
    """Every chunk id must match its content, otherwise lineage and reuse break."""
    problems = []
    for chunk_set in ctx.chunk_sets:
        for chunk in chunk_set.chunks:
            expected = make_chunk_id(
                chunk.doc_version,
                chunk.page_start,
                chunk.page_end,
                chunk.text,
                chunk_set.chunker_version,
                chunk_set.embedding_model,
            )
            if chunk.chunk_id != expected or chunk.doc_version != chunk_set.doc_version:
                problems.append(f"chunk {chunk.chunk_id} does not match its content")
    return _result("chunk_ids", problems)


def check_page_coverage(ctx: GateContext) -> CheckResult:
    """Every page of every new document version has a cleaned page."""
    seen: dict[str, set[int]] = {}
    for page in ctx.clean_pages:
        seen.setdefault(page.doc_version, set()).add(page.page_no)
    problems = []
    for chunk_set in ctx.chunk_sets:
        document = ctx.documents.get(chunk_set.doc_version)
        if document is None or document.page_count is None:
            problems.append(f"{chunk_set.doc_version} has no page count")
            continue
        missing = set(range(1, document.page_count + 1)) - seen.get(chunk_set.doc_version, set())
        if missing:
            problems.append(f"{chunk_set.doc_version} misses pages {sorted(missing)}")
    return _result("page_coverage", problems)


def check_ocr_confidence(ctx: GateContext, minimum: float) -> CheckResult:
    """Pages below the threshold need SME review before the knowledge base can publish."""
    problems = [
        f"{page.doc_version} page {page.page_no} ocr confidence {page.flags.min_ocr_conf:.2f}"
        for page in ctx.clean_pages
        if page.flags.min_ocr_conf is not None and page.flags.min_ocr_conf < minimum
    ]
    return _result("ocr_confidence", problems)


def check_pii(ctx: GateContext) -> CheckResult:
    problems = [
        f"{page.doc_version} page {page.page_no} still has {page.flags.pii_remaining} PII hits"
        for page in ctx.clean_pages
        if page.flags.pii_remaining
    ]
    return _result("pii", problems)


def check_duplicate_rate(ctx: GateContext, maximum: float) -> CheckResult:
    if not ctx.clean_pages:
        return _result("duplicate_rate", [])
    rate = sum(1 for page in ctx.clean_pages if page.flags.dup_of) / len(ctx.clean_pages)
    problems = [f"duplicate rate {rate:.2%} is above {maximum:.2%}"] if rate > maximum else []
    return _result("duplicate_rate", problems)


def check_embeddings(ctx: GateContext, dim: int) -> CheckResult:
    problems = []
    for chunk_set in ctx.chunk_sets:
        if chunk_set.embedding_model != ctx.manifest.embedding_model:
            problems.append(f"{chunk_set.doc_version} uses {chunk_set.embedding_model}")
        for chunk in chunk_set.chunks:
            vector = chunk.embedding
            if vector is None or len(vector) != dim:
                problems.append(f"chunk {chunk.chunk_id} needs a {dim} dim embedding")
            elif not all(math.isfinite(value) for value in vector):
                problems.append(f"chunk {chunk.chunk_id} has a non finite value")
            elif math.fsum(value * value for value in vector) == 0:
                problems.append(f"chunk {chunk.chunk_id} has a zero vector")
    return _result("embeddings", problems)


def check_licences(ctx: GateContext) -> CheckResult:
    problems = [
        f"{document.doc_version} is an external exercise without a licence"
        for document in ctx.documents.values()
        if document.source_type == SourceType.EXTERNAL_EXERCISE and not document.licence
    ]
    return _result("licences", problems)


def not_implemented_check(name: str) -> Check:
    """Placeholder for checks owned by another lane. It reports skipped and never blocks."""

    def check(_ctx: GateContext) -> CheckResult:
        return CheckResult(name=name, passed=False, skipped=True, details=["not implemented yet"])

    return check


def default_checks(settings: PlatformSettings) -> list[Check]:
    return [
        check_schema_versions,
        check_chunk_ids,
        check_page_coverage,
        lambda ctx: check_ocr_confidence(ctx, settings.gate_min_ocr_confidence),
        check_pii,
        lambda ctx: check_duplicate_rate(ctx, settings.gate_max_duplicate_rate),
        lambda ctx: check_embeddings(ctx, settings.embedding_dim),
        check_licences,
        not_implemented_check("retrieval_regression"),
        not_implemented_check("ragas_regression"),
    ]


def sme_required(registry: Registry, manifest: KnowledgeBaseManifest) -> bool:
    """New or corrected documents need an SME. A pure embedding refresh does not."""
    if manifest.parent_version is None:
        return True
    parent = registry.get_kb_version(manifest.parent_version)
    return bool(set(manifest.doc_versions) - set(parent.doc_versions))


def run_gate(registry: Registry, ctx: GateContext, checks: Sequence[Check]) -> GateReport:
    """Run every check, store the report and link it to the candidate."""
    if ctx.manifest.status != KnowledgeBaseStatus.CANDIDATE:
        raise VersioningError(f"version {ctx.manifest.version_id} is not a candidate")
    report = GateReport(
        report_id=f"gate-{uuid.uuid4().hex[:12]}",
        version_id=ctx.manifest.version_id,
        checks=[check(ctx) for check in checks],
        requires_sme=sme_required(registry, ctx.manifest),
        created_at=utcnow(),
    )
    registry.add_gate_report(report)
    registry.set_kb_status(ctx.manifest.version_id, KnowledgeBaseStatus.CANDIDATE, report.report_id)
    return report


def record_sme_decision(
    registry: Registry, report_id: str, *, approved: bool, by: str, comment: str | None = None
) -> GateReport:
    decision = SmeDecision.APPROVED if approved else SmeDecision.REJECTED
    registry.set_sme_decision(report_id, decision, by, comment)
    return registry.get_gate_report(report_id)


def _result(name: str, problems: list[str]) -> CheckResult:
    return CheckResult(name=name, passed=not problems, details=problems)
