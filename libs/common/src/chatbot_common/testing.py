"""Fake other services in tests, so a lane never waits for another lane to finish.

Map an endpoint to a function that receives the parsed request and returns a response record.
Samples from chatbot_contracts.samples make good return values.
"""

import json
from collections.abc import Callable, Iterable

import httpx
from pydantic import BaseModel

from chatbot_common.service import encode_event
from chatbot_contracts.escalation import StreamEvent
from chatbot_contracts.routes import Endpoint

Handler = Callable[[BaseModel], BaseModel | Iterable[StreamEvent]]


def mock_transport(handlers: dict[Endpoint, Handler]) -> httpx.MockTransport:
    by_path = {endpoint.path: (endpoint, handler) for endpoint, handler in handlers.items()}

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path not in by_path:
            return httpx.Response(404, json={"detail": f"no fake for {request.url.path}"})
        endpoint, handler = by_path[request.url.path]
        result = handler(endpoint.request.model_validate(json.loads(request.content)))
        if isinstance(result, BaseModel):
            return httpx.Response(200, json=result.model_dump(mode="json"))
        body = "".join(encode_event(event) for event in result)
        return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})

    return httpx.MockTransport(handle)


def fake_client(handlers: dict[Endpoint, Handler]) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=mock_transport(handlers), base_url="http://fake")
