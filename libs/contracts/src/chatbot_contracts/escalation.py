"""Records for Level 3 escalation and the events streamed to the student."""

from datetime import datetime

from pydantic import Field

from chatbot_contracts.base import OnlineRecord
from chatbot_contracts.enums import ConfidenceLevel, EscalationStatus, EventType
from chatbot_contracts.external import ExternalItem
from chatbot_contracts.query import Citation


class EscalationTicket(OnlineRecord):
    """Created when an answer lands at L3. The question is already pseudonymized."""

    ticket_id: str
    pseudo_user: str
    question: str
    confidence: float = Field(ge=0.0, le=1.0)
    status: EscalationStatus
    created_at: datetime
    context_ids: list[str] = Field(default_factory=list)
    external_results: list[ExternalItem] = Field(default_factory=list)
    expert: str | None = None
    answered_at: datetime | None = None
    answer: str | None = None


class StreamEvent(OnlineRecord):
    """One server sent event from the gateway to the student frontend."""

    type: EventType
    text: str = ""
    citations: list[Citation] = Field(default_factory=list)
    level: ConfidenceLevel | None = None
