# Gateway

The only public entry of the backend. It covers step 1 and step 10 of the query path in [ARCHITECTURE.md](../../docs/architecture/ARCHITECTURE.md), section 5.

**Owner:** Lane C.
**Public API (for the existing student frontend):**
- `POST /v1/ask`: multipart form with `question` and an optional `file`, plus an `Authorization: Bearer` header. It answers with server-sent events, one `StreamEvent` per event.
- `GET /v1/answers/{request_id}`: the late expert answer of an escalated question.

**Calls:** the orchestrator (`routes.ANSWER`) and the escalation service.

## Files

- `serve.py`: routes, already wired.
- `ask.py`: the flow, in the order listed in its docstring.
- `auth.py`, `pseudonym.py`, `guard.py`, `limits.py`, `uploads.py`: one concern each.
- `settings.py`: `GATEWAY_*` variables.

## Start here

1. `ask.handle_ask` with every dependency faked, relaying sample events from a fake orchestrator (`chatbot_common.testing.fake_client`).
2. `limits`, `uploads` (with `make_test_platform`), then `auth` and `pseudonym`.
3. `guard` last. Until then, return a safe verdict behind a setting that is off in production.

## Test

```bash
uv run --package chatbot-gateway pytest services/gateway/tests
```
