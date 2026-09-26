"""Public HTTP API for the student frontend.

POST /v1/ask takes a multipart form with a question, an optional conversation id and an optional
file, and answers with server sent events carrying StreamEvent records. GET /v1/answers/{request_id}
returns the late expert answer of an escalated question once it exists.
router holds the public routes. The api service mounts it, and app serves it alone in tests.
"""

from typing import Annotated

from fastapi import APIRouter, File, Form, Header, UploadFile
from fastapi.responses import StreamingResponse

from chatbot_common.service import create_app
from chatbot_contracts.escalation import EscalationTicket
from chatbot_gateway.ask import fetch_late_answer, handle_ask

ASK_PATH = "/v1/ask"
LATE_ANSWER_PATH = "/v1/answers/{request_id}"

router = APIRouter()


@router.post(ASK_PATH)
async def ask(
    question: Annotated[str, Form()],
    authorization: Annotated[str, Header()],
    conversation_id: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
) -> StreamingResponse:
    return await handle_ask(question, conversation_id, file, authorization)


@router.get(LATE_ANSWER_PATH, response_model=EscalationTicket)
async def late_answer(request_id: str, authorization: Annotated[str, Header()]) -> EscalationTicket:
    return await fetch_late_answer(request_id, authorization)


app = create_app("gateway")
app.include_router(router)
