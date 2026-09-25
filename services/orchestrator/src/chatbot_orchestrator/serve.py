"""HTTP entrypoint of the orchestrator. The gateway is its only caller."""

from fastapi.responses import StreamingResponse

from chatbot_common.service import create_app, sse_response
from chatbot_contracts.query import AskRequest
from chatbot_contracts.routes import ANSWER
from chatbot_orchestrator.pipeline import answer

app = create_app("orchestrator")


@app.post(ANSWER.path)
async def ask(request: AskRequest) -> StreamingResponse:
    return sse_response(answer(request))
