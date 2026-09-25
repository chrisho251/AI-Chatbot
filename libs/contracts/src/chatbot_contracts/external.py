"""Records for W7 external web search and the enrichment candidate queue."""

from pydantic import Field

from chatbot_contracts.base import Model, OnlineRecord, Record
from chatbot_contracts.enums import CandidateOrigin, CandidateStatus


class ExternalItem(Model):
    """One page found on an allowlisted external source. Always shown as unvetted."""

    url: str
    title: str
    snippet: str
    score: float
    licence: str | None = None
    snapshot_uri: str | None = None


class ExternalSearchRequest(OnlineRecord):
    """The query must already be PII stripped by W5."""

    query: str
    topics: list[str] = Field(default_factory=list)
    max_results: int = Field(default=5, ge=1, le=20)


class ExternalSearchResult(OnlineRecord):
    items: list[ExternalItem]
    timings_ms: dict[str, float] = Field(default_factory=dict)


class ExternalCandidate(Record):
    """An external find waiting for SME triage before it may enter the corpus."""

    candidate_id: str
    url: str
    snapshot_sha256: str
    found_by: CandidateOrigin
    status: CandidateStatus = CandidateStatus.PENDING
    licence: str | None = None
    course_code: str | None = None
    topic: str | None = None
