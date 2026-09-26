"""Records of the online plane, from a student question to a cited answer."""

from pydantic import Field

from chatbot_contracts.base import Model, OnlineRecord
from chatbot_contracts.enums import CleanOrigin
from chatbot_contracts.external import ExternalItem
from chatbot_contracts.tools import ToolCallRecord


class Attachment(OnlineRecord):
    """A file the student sent with the question, stored in the uploads bucket."""

    attachment_id: str
    media_type: str
    uri: str
    sha256: str
    size_bytes: int = Field(ge=0)


class AskRequest(OnlineRecord):
    """A pseudonymized question the gateway forwards to the orchestrator.

    conversation_id groups the questions of one chat. The gateway creates it for a new chat, the
    orchestrator uses it to read the earlier turns.
    """

    pseudo_user: str
    conversation_id: str
    question: str
    attachments: list[Attachment] = Field(default_factory=list)


class VisionRequest(OnlineRecord):
    attachment: Attachment


class VisionResult(OnlineRecord):
    text: str
    latex: list[str] = Field(default_factory=list)
    detected_kind: str
    confidence: float = Field(ge=0.0, le=1.0)


class CleanRequest(OnlineRecord):
    text: str
    origin: CleanOrigin


class CleanResult(OnlineRecord):
    """dropped is true when the text must not reach the model, such as after an injection hit."""

    text: str
    pii_hits: int = Field(default=0, ge=0)
    injection_hits: int = Field(default=0, ge=0)
    dropped: bool = False


class EmbedRequest(OnlineRecord):
    texts: list[str]
    kb_version: int


class EmbedResult(OnlineRecord):
    vectors: list[list[float]]
    embedding_model: str


class RetrievalRequest(OnlineRecord):
    question: str
    query_vector: list[float]
    kb_version: int
    k: int = Field(default=8, ge=1, le=50)
    filters: dict[str, str] = Field(default_factory=dict)


class RetrievedChunk(Model):
    """A chunk with the score of each retrieval stage that saw it."""

    chunk_id: str
    doc_version: str
    page_start: int
    page_end: int
    text: str
    dense: float | None = None
    lexical: float | None = None
    rerank: float | None = None


class RetrievalResult(OnlineRecord):
    """sufficiency is the top rerank score adjusted by its margin, from 0 to 1."""

    chunks: list[RetrievedChunk]
    sufficiency: float = Field(ge=0.0, le=1.0)
    timings_ms: dict[str, float] = Field(default_factory=dict)


class Citation(Model):
    """Points at a knowledge base chunk, or at an external url for unvetted sources."""

    chunk_id: str | None = None
    url: str | None = None
    doc_version: str | None = None
    page: int | None = None


class Turn(Model):
    """One earlier question and its answer in the same conversation."""

    question: str
    answer: str


class GenerationRequest(OnlineRecord):
    """question is the standalone question. history holds the earlier turns, oldest first."""

    question: str
    contexts: list[RetrievedChunk]
    model_version: str
    prompt_version: str
    external_contexts: list[ExternalItem] = Field(default_factory=list)
    history: list[Turn] = Field(default_factory=list)


class GenerationResult(OnlineRecord):
    answer: str
    citations: list[Citation]
    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    timings_ms: dict[str, float] = Field(default_factory=dict)
