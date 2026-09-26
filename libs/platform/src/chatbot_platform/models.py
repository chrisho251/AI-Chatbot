"""Records that stay inside the platform. Cross component records live in chatbot_contracts."""

from datetime import datetime
from enum import StrEnum

from chatbot_contracts.base import Model
from chatbot_contracts.knowledge_base import Chunk

SERVING_ALIAS = "serving"
CANDIDATE_ALIAS = "candidate"


class RunStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class SmeDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


class StoredChunk(Model):
    """A chunk in the serving index with the lineage columns written at publish time."""

    chunk: Chunk
    ingestion_run_id: str
    embedding_model: str
    chunker_version: str


class IndexHit(Model):
    chunk: StoredChunk
    score: float


class CheckResult(Model):
    """Outcome of one quality gate check. A skipped check neither passes nor blocks."""

    name: str
    passed: bool
    skipped: bool = False
    details: list[str] = []


class GateReport(Model):
    report_id: str
    version_id: int
    checks: list[CheckResult]
    requires_sme: bool
    created_at: datetime
    sme_decision: SmeDecision | None = None
    sme_by: str | None = None
    sme_comment: str | None = None
    sme_at: datetime | None = None

    @property
    def auto_passed(self) -> bool:
        return all(check.passed or check.skipped for check in self.checks)

    @property
    def approved(self) -> bool:
        """True when publication is allowed."""
        if not self.auto_passed:
            return False
        return not self.requires_sme or self.sme_decision == SmeDecision.APPROVED


class LineageTrace(Model):
    """Where a cited chunk came from, down to the raw file."""

    chunk_id: str
    doc_version: str
    page_start: int
    page_end: int
    region_ids: list[str]
    ingestion_run_id: str
    raw_sha256: str
    raw_uri: str
    source_url: str | None
    licence: str | None


class CorrectionFlag(Model):
    """A past answer that cited a chunk whose source was corrected or retracted since."""

    request_id: str
    chunk_id: str
    doc_version: str
    superseded_by: str | None
