"""FastAPI app factory, contract routes and server sent events helper.

Every service starts from create_app, so health checks, metrics and error handling look the same
everywhere. Code that is not written yet raises NotImplementedError, and the app answers 501 for it.
add_contract_routes serves the local handlers of a component over HTTP, so a worker answers the
same way inside the api process and in its own container.
Prometheus scrapes the metrics route of every service, see chatbot_common.metrics.
"""

import inspect
import json
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from chatbot_common.http import LocalHandler
from chatbot_common.metrics import HTTP_DURATION, exposition
from chatbot_contracts.escalation import StreamEvent
from chatbot_contracts.routes import Endpoint

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


def add_contract_routes(app: FastAPI, handlers: Mapping[Endpoint, LocalHandler]) -> None:
    """Register one POST route per endpoint. Streamed endpoints answer with server sent events."""
    for endpoint, handler in handlers.items():
        streaming = endpoint.response is StreamEvent
        app.add_api_route(
            endpoint.path,
            _contract_route(endpoint, handler, streaming),
            methods=["POST"],
            response_model=None if streaming else endpoint.response,
            name=endpoint.path,
        )


def _contract_route(
    endpoint: Endpoint, handler: LocalHandler, streaming: bool
) -> Callable[..., Awaitable[object]]:
    async def route(request: object) -> object:
        if streaming:
            return sse_response(handler(request))
        return await handler(request)

    parameter = inspect.Parameter(
        "request", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=endpoint.request
    )
    route.__signature__ = inspect.Signature([parameter])  # type: ignore[attr-defined]
    return route


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
