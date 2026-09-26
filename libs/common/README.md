# chatbot-common

Helpers every service and worker shares. Nothing here knows about a specific worker.

**Owner:** Lane A for `service.py`, `http.py`, `testing.py`, `settings.py`, `keys.py`. Lane C for `llm.py`. Lane B for `embeddings.py`. Lane D for `telemetry.py`.
**Depends on:** chatbot-contracts, FastAPI, httpx.

## What is inside

- `service.py`: `create_app(name)` gives every service `/health`, `/metrics` with the duration of every route, and turns `NotImplementedError` into HTTP 501. `add_contract_routes(app, HANDLERS)` serves a component's handlers over HTTP. `sse_response` streams `StreamEvent`s.
- `metrics.py`: the metric catalogue. Define a metric here before recording it or using it in a dashboard. Who records what is in [docs/MONITORING.md](../../docs/MONITORING.md).
- `http.py`: `ContractClient.call(endpoint, request)` and `ContractClient.stream(...)`, typed by `chatbot_contracts.routes`. An endpoint with a local handler is a function call in the same process, every other endpoint goes over HTTP. `shared_client()` is the client to use in services and workers. `register_local(handlers)` is called once by the api service.
- `testing.py`: `fake_client({endpoint: handler})` fakes another service in tests. Return samples from `chatbot_contracts.samples`.
- `llm.py`: `ChatClient` for the OpenAI-compatible API of llama.cpp and vLLM.
- `embeddings.py`: `Embedder` and `Reranker` protocols with TEI clients.
- `settings.py`: `ServiceSettings` (`CHATBOT_*` variables) and `service_url`, used only for components that run in their own container.
- `keys.py`: the `KeyService` port for pseudonyms and text encryption. `FileKeyService` reads the local key file, KMS replaces it on AWS.
- `telemetry.py`: stub for OpenTelemetry traces.

## Calling another lane before it exists

Give the client a local handler that returns a sample. This is exactly how the api service calls a real worker.

```python
from chatbot_common.http import ContractClient
from chatbot_contracts import routes, samples


async def retrieve(request):
    return samples.sample_retrieval_result()


client = ContractClient(local={routes.RETRIEVE: retrieve})
result = await client.call(routes.RETRIEVE, samples.sample_retrieval_request())
```

To test the HTTP path instead, build the client on `fake_client({routes.RETRIEVE: lambda req: samples.sample_retrieval_result()})`.

## Test

```bash
uv run --package chatbot-common pytest libs/common/tests
```
