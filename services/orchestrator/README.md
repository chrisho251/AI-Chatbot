# Query orchestrator

Runs steps 2 to 9 of the query path in [ARCHITECTURE.md](../../docs/architecture/ARCHITECTURE.md), section 5: conversation history, input preparation, retrieval, generation, citation validation, confidence and L1/L2/L3 routing.

**Owner:** Lane C.
**Endpoint:** `POST /v1/answer`, `AskRequest` in, server-sent `StreamEvent`s out (`routes.ANSWER`).
**Calls:** W2, W5, W6, W7, W8 and the escalation service, always through `shared_client()` and `chatbot_contracts.routes`.
**Runs in:** the api service, which calls `serve.HANDLERS` in process. `serve.app` serves the same handler over HTTP for tests.

## Files

- `pipeline.py`: the flow, step by step in its docstring.
- `confidence.py`, `citations.py`, `groundedness.py`: scoring.
- `conversation.py`: earlier turns and the standalone question for follow-ups.
- `interactions.py`: logging to `ops.*`.
- `settings.py`: thresholds (placeholders).

## Start here

`pipeline.answer` with a `ContractClient` whose local handlers return samples for every endpoint. You can build and test the whole orchestration, including the L3 path, before any worker exists.

## Test

```bash
uv run --package chatbot-orchestrator pytest services/orchestrator/tests
```
