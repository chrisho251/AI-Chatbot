# Query orchestrator

Runs steps 2 to 9 of the query path in [ARCHITECTURE.md](../../docs/architecture/ARCHITECTURE.md), section 5: input preparation, retrieval, generation, citation validation, confidence and L1/L2/L3 routing.

**Owner:** Lane C.
**Endpoint:** `POST /v1/answer`, `AskRequest` in, server-sent `StreamEvent`s out (`routes.ANSWER`).
**Calls:** W2, W5, W6, W7, W8 and the escalation service, always through `ContractClient` and `chatbot_contracts.routes`.

## Files

- `pipeline.py`: the flow, step by step in its docstring.
- `confidence.py`, `citations.py`, `groundedness.py`: scoring.
- `interactions.py`: logging to `ops.*`.
- `settings.py`: thresholds (placeholders).

## Start here

`pipeline.answer` with `fake_client` returning samples for every endpoint. You can build and test the whole orchestration, including the L3 path, before any worker exists.

## Test

```bash
uv run --package chatbot-orchestrator pytest services/orchestrator/tests
```
