"""Typed client for calling another component through an Endpoint from chatbot_contracts.routes.

An endpoint with a local handler is called as a plain function in this process. That is how the
api service runs the gateway, orchestrator, escalation and workers together without HTTP between
them. Every other endpoint goes over HTTP to service_url. Both paths record WORKER_CALL, so the
time spent in each worker shows on the dashboards either way.
In tests pass an httpx.AsyncClient built with testing.mock_transport, or with an ASGI transport
around the real app, so no server needs to run.
"""

import time
from collections.abc import AsyncIterator, Callable, Mapping
from functools import cache
from typing import Any

import httpx
from pydantic import BaseModel

from chatbot_common.metrics import WORKER_CALL
from chatbot_common.settings import service_url
from chatbot_contracts.escalation import StreamEvent
from chatbot_contracts.routes import Endpoint

LocalHandler = Callable[[Any], Any]
"""An async function from the request record to the response record. For endpoints that stream
StreamEvent records, a function that returns an async iterator of them."""

_LOCAL_HANDLERS: dict[Endpoint, LocalHandler] = {}


class ContractClient:
    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        timeout_s: float = 60.0,
        local: Mapping[Endpoint, LocalHandler] | None = None,
    ) -> None:
        self._client = client or httpx.AsyncClient(timeout=timeout_s)
        self._local = local if local is not None else {}

    def _url(self, endpoint: Endpoint) -> str:
        base = "" if str(self._client.base_url) else service_url(endpoint.service)
        return base + endpoint.path

    async def call[Req: BaseModel, Resp: BaseModel](
        self, endpoint: Endpoint[Req, Resp], request: Req
    ) -> Resp:
        start = time.perf_counter()
        try:
            handler = self._local.get(endpoint)
            if handler is not None:
                return await handler(request)
            response = await self._client.post(
                self._url(endpoint), json=request.model_dump(mode="json")
            )
            response.raise_for_status()
            return endpoint.response.model_validate(response.json())
        finally:
            _observe(endpoint, start)

    async def stream[Req: BaseModel](
        self, endpoint: Endpoint[Req, StreamEvent], request: Req
    ) -> AsyncIterator[StreamEvent]:
        start = time.perf_counter()
        try:
            handler = self._local.get(endpoint)
            if handler is not None:
                async for event in handler(request):
                    yield event
                return
            payload = request.model_dump(mode="json")
            async with self._client.stream("POST", self._url(endpoint), json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield StreamEvent.model_validate_json(line.removeprefix("data: "))
        finally:
            _observe(endpoint, start)

    async def aclose(self) -> None:
        await self._client.aclose()


def _observe(endpoint: Endpoint, start: float) -> None:
    WORKER_CALL.labels(endpoint.service, endpoint.path).observe(time.perf_counter() - start)


def register_local(handlers: Mapping[Endpoint, LocalHandler]) -> None:
    """Serve these endpoints in this process. The api service calls it once when it starts."""
    _LOCAL_HANDLERS.update(handlers)


@cache
def shared_client() -> ContractClient:
    """The client every service and worker uses. It sees handlers registered later as well."""
    return ContractClient(local=_LOCAL_HANDLERS)
