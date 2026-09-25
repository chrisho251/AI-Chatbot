# chatbot-common

Helpers every service and worker shares. Nothing here knows about a specific worker.

**Owner:** Lane A for `service.py`, `http.py`, `testing.py`, `settings.py`. Lane C for `llm.py`. Lane B for `embeddings.py`. Lane D for `telemetry.py`.
**Depends on:** chatbot-contracts, FastAPI, httpx.

## What is inside

- `service.py`: `create_app(name)` gives every service `/health`, `/metrics` with the duration of every route, and turns `NotImplementedError` into HTTP 501. `sse_response` streams `StreamEvent`s.
- `metrics.py`: the metric catalogue. Define a metric here before recording it or using it in a dashboard. Who records what is in [docs/MONITORING.md](../../docs/MONITORING.md).
- `http.py`: `ContractClient.call(endpoint, request)` and `ContractClient.stream(...)`, typed by `chatbot_contracts.routes`.
- `testing.py`: `fake_client({endpoint: handler})` fakes another service in tests. Return samples from `chatbot_contracts.samples`.
- `llm.py`: `ChatClient` for the OpenAI-compatible API of llama.cpp and vLLM.
- `embeddings.py`: `Embedder` and `Reranker` protocols with TEI clients.
- `settings.py`: `ServiceSettings` (`CHATBOT_*` variables) and `service_url`.
- `telemetry.py`: stub for OpenTelemetry traces.

## Calling another lane before it exists

```python
from chatbot_common.http import ContractClient
from chatbot_common.testing import fake_client
from chatbot_contracts import routes, samples

client = ContractClient(
    fake_client({routes.RETRIEVE: lambda req: samples.sample_retrieval_result()})
)
result = await client.call(routes.RETRIEVE, samples.sample_retrieval_request())
```

## Test

```bash
uv run --package chatbot-common pytest libs/common/tests
```
