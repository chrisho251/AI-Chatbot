"""HTTP entrypoint of W8 gen. Routes come from chatbot_contracts.routes."""

from fastapi.responses import StreamingResponse

from chatbot_common.service import create_app, sse_response
from chatbot_contracts.query import GenerationRequest, GenerationResult
from chatbot_contracts.routes import GENERATE, GENERATE_STREAM
from chatbot_w8_gen.generate import generate, generate_stream

app = create_app("w8_gen")


@app.post(GENERATE.path, response_model=GenerationResult)
async def generate_route(request: GenerationRequest) -> GenerationResult:
    return await generate(request)


@app.post(GENERATE_STREAM.path)
async def generate_stream_route(request: GenerationRequest) -> StreamingResponse:
    return sse_response(generate_stream(request))
