import json

import httpx
from fastapi.testclient import TestClient

from chatbot_common.embeddings import TeiEmbedder, TeiReranker
from chatbot_common.http import ContractClient, register_local, shared_client
from chatbot_common.llm import ChatClient
from chatbot_common.service import add_contract_routes, create_app, decode_events, sse_response
from chatbot_common.settings import service_url
from chatbot_common.testing import fake_client
from chatbot_contracts import routes, samples
from chatbot_contracts.enums import EventType


def test_app_has_health_and_answers_501_for_unwritten_code():
    app = create_app("w4_math")

    @app.post("/todo")
    async def todo():
        raise NotImplementedError("later")

    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok", "service": "w4_math"}
    assert client.post("/todo").status_code == 501


def test_sse_response_round_trips_events():
    app = create_app("w8_gen")
    events = [
        samples.sample_stream_event(),
        samples.sample_stream_event(type=EventType.ANSWER_FINAL),
    ]

    @app.post("/stream")
    async def stream():
        async def produce():
            for event in events:
                yield event

        return sse_response(produce())

    assert decode_events(TestClient(app).post("/stream").text) == events


async def test_contract_client_calls_a_fake_service():
    client = ContractClient(
        fake_client({routes.CALC: lambda request: samples.sample_calc_result(value=9.0)})
    )
    result = await client.call(routes.CALC, samples.sample_calc_check())
    assert result.value == 9.0


async def test_contract_client_reads_a_stream():
    events = [samples.sample_stream_event(text="a"), samples.sample_stream_event(text="b")]
    client = ContractClient(fake_client({routes.ANSWER: lambda request: events}))
    received = [event async for event in client.stream(routes.ANSWER, samples.sample_ask_request())]
    assert received == events


async def test_local_handlers_are_called_without_http():
    async def calc(request):
        return samples.sample_calc_result(value=request.variables.get("x", 0.0))

    async def answer(request):
        yield samples.sample_stream_event(text=request.question)

    client = ContractClient(local={routes.CALC: calc, routes.ANSWER: answer})
    result = await client.call(routes.CALC, samples.sample_calc_check(variables={"x": 2.0}))
    received = [event async for event in client.stream(routes.ANSWER, samples.sample_ask_request())]
    assert result.value == 2.0
    assert [event.text for event in received] == [samples.sample_ask_request().question]


async def test_shared_client_sees_handlers_registered_later():
    async def vision(request):
        return samples.sample_vision_result()

    client = shared_client()
    register_local({routes.VISION: vision})
    assert await client.call(routes.VISION, samples.sample_vision_request()) == (
        samples.sample_vision_result()
    )


def test_contract_routes_serve_the_same_handlers_over_http():
    async def calc(request):
        return samples.sample_calc_result(value=9.0)

    def answer(request):
        async def events():
            yield samples.sample_stream_event()

        return events()

    app = create_app("w4_math")
    add_contract_routes(app, {routes.CALC: calc, routes.ANSWER: answer})
    client = TestClient(app)
    calc_body = samples.sample_calc_check().model_dump(mode="json")
    assert client.post(routes.CALC.path, json=calc_body).json()["value"] == 9.0
    ask_body = samples.sample_ask_request().model_dump(mode="json")
    streamed = decode_events(client.post(routes.ANSWER.path, json=ask_body).text)
    assert streamed == [samples.sample_stream_event()]
    assert client.post(routes.CALC.path, json={"operation": 1}).status_code == 422


def test_service_url_uses_override_or_compose_name(monkeypatch):
    assert service_url("w7_deepsearch") == "http://w7-deepsearch:8000"
    monkeypatch.setenv("CHATBOT_W7_DEEPSEARCH_URL", "http://localhost:9007")
    assert service_url("w7_deepsearch") == "http://localhost:9007"


async def test_chat_client_complete_and_stream():
    def handle(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if body.get("stream"):
            chunks = [{"choices": [{"delta": {"content": piece}}]} for piece in ("Hel", "lo")]
            text = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks) + "data: [DONE]\n\n"
            return httpx.Response(200, text=text)
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Hello"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 1},
            },
        )

    client = ChatClient(
        "http://llm/v1", "model", httpx.AsyncClient(transport=httpx.MockTransport(handle))
    )
    completion = await client.complete([{"role": "user", "content": "hi"}])
    assert (completion.text, completion.tokens_in, completion.tokens_out) == ("Hello", 5, 1)
    assert [piece async for piece in client.stream([{"role": "user", "content": "hi"}])] == [
        "Hel",
        "lo",
    ]


async def test_tei_clients():
    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/embed":
            return httpx.Response(200, json=[[0.1, 0.2]])
        return httpx.Response(200, json=[{"index": 1, "score": 0.9}, {"index": 0, "score": 0.2}])

    http = httpx.AsyncClient(transport=httpx.MockTransport(handle))
    assert await TeiEmbedder("http://tei", "bge-m3", http).embed(["x"]) == [[0.1, 0.2]]
    assert await TeiReranker("http://tei", http).rerank("q", ["a", "b"]) == [0.2, 0.9]


def test_metrics_record_route_templates_but_not_health():
    app = create_app("w7_deepsearch")

    @app.get("/v1/items/{item_id}")
    async def item(item_id: str):
        return {"id": item_id}

    client = TestClient(app)
    client.get("/v1/items/42")
    client.get("/health")
    body = client.get("/metrics").text
    assert 'route="/v1/items/{item_id}"' in body
    assert 'service="w7_deepsearch"' in body
    assert 'route="/health"' not in body
    assert "chatbot_requests_total" in body
    assert "chatbot_worker_call_seconds" in body
