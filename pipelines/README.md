# Pipelines

The Dagster code location of the offline plane: ingestion, quality gate and publish, retention, lineage sweep, history snapshots, enrichment and scheduled evaluation.

**Owner:** Lane A.
**Depends on:** `chatbot-platform` only. Worker code is never imported: each worker runs in its own image through Dagster Pipes (`steps.py`).

## Files

- `definitions.py`: the code location (`defs`).
- `steps.py`: run a worker step in its image.
- `ingestion.py`: ingest, build and gate, publish.
- `sensors.py`, `schedules.py`, `snapshots.py`.

## Start here

1. `ingestion.py` with a fake `run_step` that writes sample rows into `make_test_platform`. This proves the whole publish flow before any worker is done.
2. `steps.run_step` with a tiny echo image.
3. Sensors and schedules.

## Run locally

```bash
docker compose --profile data --profile pipeline up -d
```

Then open http://localhost:3000.

## Test

```bash
uv run --package chatbot-pipelines pytest pipelines/tests
```
