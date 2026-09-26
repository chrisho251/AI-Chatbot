# API service

The whole online plane in one FastAPI process: the gateway, the query orchestrator, the escalation service and the online roles of W2 to W8. See [ARCHITECTURE.md](../../docs/architecture/ARCHITECTURE.md), section 2.

**Owner:** Lane C, with Lane A for the image.
**Public routes:** the gateway routes (`POST /v1/ask`, `GET /v1/answers/{request_id}`) and the expert route of the escalation service (`POST /v1/tickets/{ticket_id}/answer`). Traefik exposes only these.
**Runs as:** `uvicorn chatbot_api.serve:app`, the `api` service in the `core` compose profile.

## How it works

- Every component keeps its own package, contracts, tests and lane owner. Each `serve.py` exposes `HANDLERS`, a map from a `chatbot_contracts.routes` endpoint to the function that answers it.
- `serve.py` here registers all of them with `chatbot_common.http.register_local`. Components call each other with `shared_client()`, so a call is a plain function call with the same request and response records. `ContractClient` still records `chatbot_worker_call_seconds` for every call.
- The internal contract endpoints are not served over HTTP by this app. Only the public routes are.
- The image holds every service and worker package. Dagster starts the same image with a worker job command, for example `chatbot-w1-ingest-job`, for each offline step.

## Move one component to its own container

Run its standalone app from this image, for example `uvicorn chatbot_w2_vision.serve:app`, and set `CHATBOT_W2_VISION_URL` for the api service. The api then leaves that component's handlers out and calls it over HTTP. Nothing else changes.

## Rules

- CPU heavy work, such as a classifier, SymPy or Presidio, runs with `asyncio.to_thread`, so one request never blocks the others.
- Never import one service or worker from another. Only this package imports them, and `scripts/check_boundaries.py` enforces it.

## Test

```bash
uv run --package chatbot-api pytest services/api/tests
```

This installs every worker, torch and Docling included.
