"""FastAPI app factory and server sent events helper.

Every service starts from create_app, so health checks, metrics and error handling look the same
everywhere. Code that is not written yet raises NotImplementedError, and the app answers 501 for it.
Prometheus scrapes the metrics route of every service, see chatbot_common.metrics.
"""

import json
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from chatbot_common.metrics import HTTP_DURATION, exposition
from chatbot_contracts.escalation import StreamEvent

SSE_MEDIA_TYPE = "text/event-stream"
UNTRACKED_PATHS = frozenset({"/health", "/metrics"})


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app(service: str) -> FastAPI:
    app = FastAPI(title=service)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": service}

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        body, content_type = exposition()
        return Response(body, media_type=content_type)

    @app.middleware("http")
    async def record_duration(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        route = getattr(request.scope.get("route"), "path", "unmatched")
        if route not in UNTRACKED_PATHS:
            HTTP_DURATION.labels(service, route, request.method, str(response.status_code)).observe(
                time.perf_counter() - start
            )
        return response

    @app.exception_handler(NotImplementedError)
    async def not_implemented(_request: Request, error: NotImplementedError) -> JSONResponse:
        return JSONResponse(status_code=501, content={"detail": str(error) or "not implemented"})

    return app


def encode_event(event: StreamEvent) -> str:
    return f"event: {event.type}\ndata: {event.model_dump_json()}\n\n"


def sse_response(events: AsyncIterator[StreamEvent]) -> StreamingResponse:
    async def body() -> AsyncIterator[str]:
        async for event in events:
            yield encode_event(event)

    return StreamingResponse(body(), media_type=SSE_MEDIA_TYPE)


def decode_events(text: str) -> list[StreamEvent]:
    """Parse a complete SSE body. Clients reading a live stream use ContractClient.stream."""
    return [
        StreamEvent.model_validate(json.loads(line.removeprefix("data: ")))
        for line in text.splitlines()
        if line.startswith("data: ")
    ]
