"""HTTP endpoints of every online component, with their request and response records.

Servers register routes from these definitions and clients call them, so paths never drift.
Endpoints whose response is StreamEvent send server sent events instead of one JSON body.
"""

from dataclasses import dataclass

from pydantic import BaseModel

from chatbot_contracts.escalation import EscalationTicket, StreamEvent
from chatbot_contracts.external import ExternalSearchRequest, ExternalSearchResult
from chatbot_contracts.query import (
    AskRequest,
    CleanRequest,
    CleanResult,
    EmbedRequest,
    EmbedResult,
    GenerationRequest,
    GenerationResult,
    RetrievalRequest,
    RetrievalResult,
    VisionRequest,
    VisionResult,
)
from chatbot_contracts.tools import CalcCheck, CalcResult, CodeResult, CodeTask


@dataclass(frozen=True)
class Endpoint[Req: BaseModel, Resp: BaseModel]:
    service: str
    path: str
    request: type[Req]
    response: type[Resp]


ANSWER = Endpoint("orchestrator", "/v1/answer", AskRequest, StreamEvent)
VISION = Endpoint("w2_vision", "/v1/vision", VisionRequest, VisionResult)
CODE = Endpoint("w3_code", "/v1/code", CodeTask, CodeResult)
CALC = Endpoint("w4_math", "/v1/calc", CalcCheck, CalcResult)
CLEAN = Endpoint("w5_clean", "/v1/clean", CleanRequest, CleanResult)
EMBED = Endpoint("w6_embed", "/v1/embed", EmbedRequest, EmbedResult)
RETRIEVE = Endpoint("w7_deepsearch", "/v1/retrieve", RetrievalRequest, RetrievalResult)
EXTERNAL_SEARCH = Endpoint(
    "w7_deepsearch", "/v1/external", ExternalSearchRequest, ExternalSearchResult
)
GENERATE = Endpoint("w8_gen", "/v1/generate", GenerationRequest, GenerationResult)
GENERATE_STREAM = Endpoint("w8_gen", "/v1/generate/stream", GenerationRequest, StreamEvent)
OPEN_TICKET = Endpoint("escalation", "/v1/tickets", EscalationTicket, EscalationTicket)

ALL_ENDPOINTS = (
    ANSWER,
    VISION,
    CODE,
    CALC,
    CLEAN,
    EMBED,
    RETRIEVE,
    EXTERNAL_SEARCH,
    GENERATE,
    GENERATE_STREAM,
    OPEN_TICKET,
)
