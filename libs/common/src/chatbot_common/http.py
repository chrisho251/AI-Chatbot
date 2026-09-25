"""Typed client for calling another service through an Endpoint from chatbot_contracts.routes.

In tests pass an httpx.AsyncClient built with testing.mock_transport, or with an ASGI transport
around the real app, so no server needs to run.
"""

from collections.abc import AsyncIterator

import httpx
from pydantic import BaseModel

from chatbot_common.settings import service_url
from chatbot_contracts.escalation import StreamEvent
from chatbot_contracts.routes import Endpoint


class ContractClient:
    def __init__(self, client: httpx.AsyncClient | None = None, timeout_s: float = 60.0) -> None:
        self._client = client or httpx.AsyncClient(timeout=timeout_s)

    def _url(self, endpoint: Endpoint) -> str:
        base = "" if str(self._client.base_url) else service_url(endpoint.service)
        return base + endpoint.path

    async def call[Req: BaseModel, Resp: BaseModel](
        self, endpoint: Endpoint[Req, Resp], request: Req
    ) -> Resp:
        response = await self._client.post(
            self._url(endpoint), json=request.model_dump(mode="json")
        )
        response.raise_for_status()
        return endpoint.response.model_validate(response.json())

    async def stream[Req: BaseModel](
        self, endpoint: Endpoint[Req, StreamEvent], request: Req
    ) -> AsyncIterator[StreamEvent]:
        payload = request.model_dump(mode="json")
        async with self._client.stream("POST", self._url(endpoint), json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield StreamEvent.model_validate_json(line.removeprefix("data: "))

    async def aclose(self) -> None:
        await self._client.aclose()
