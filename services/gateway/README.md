# Gateway

The only public entry of the backend. It covers step 1 and step 10 of the query path in [ARCHITECTURE.md](../../docs/architecture/ARCHITECTURE.md), section 5.

**Owner:** Lane C.
**Public API (for the existing student frontend):**
- `POST /v1/ask`: multipart form with `question`, an optional `conversation_id` and an optional `file`, plus an `Authorization: Bearer` header. It answers with server-sent events, one `StreamEvent` per event. Every event carries the `conversation_id` to send with the next question.
- `GET /v1/answers/{request_id}`: the late expert answer of an escalated question.

**Calls:** the orchestrator (`routes.ANSWER`) and the escalation service (`routes.GET_TICKET`), through `shared_client()`. In the api process these are function calls.
**Runs in:** the api service, which mounts `serve.router`. `serve.app` serves the gateway alone for tests.

## Files

- `serve.py`: the public routes in `router`, already wired.
- `ask.py`: the flow, in the order listed in its docstring.
- `auth.py`, `pseudonym.py`, `guard.py`, `limits.py`, `uploads.py`: one concern each.
- `settings.py`: `GATEWAY_*` variables.

## Start here

1. `ask.handle_ask` with every dependency faked, relaying sample events from a `ContractClient` whose local handler for `routes.ANSWER` yields samples.
2. `limits`, `uploads` (with `make_test_platform`), then `auth` and `pseudonym` (with `chatbot_common.keys.FileKeyService`).
3. `guard` last. Until then, return a safe verdict behind a setting that is off in production.

## Test

```bash
uv run --package chatbot-gateway pytest services/gateway/tests
```
