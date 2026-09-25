# chatbot-platform

The data platform: object store, registry, serving index, Iceberg lake, versioning, quality gate, lineage and retention. The design is in [docs/architecture/ARCHITECTURE.md](../../docs/architecture/ARCHITECTURE.md), section 4.

**Owner:** Lane A.
**Depends on:** chatbot-contracts.
**Status:** implemented and tested. `aws.py` and `query_engine.py` are stubs for later milestones.

## Modules

- `settings.py`: `PlatformSettings`, read from `PLATFORM_*` environment variables. Bucket names.
- `storage.py`: `ObjectStore` port, `LocalFsObjectStore` (tests) and `S3ObjectStore` (SeaweedFS locally, S3 on AWS).
- `sql.py`: SQL tables. `registry` and `ops` are portable (SQLite in tests), `serving` is Postgres only.
- `registry.py`: `Registry` for document versions, ingestion runs, corpus versions, aliases and gate reports.
- `index.py`: `ServingIndex` port and `InMemoryServingIndex`. `pg_index.py`: `PgServingIndex` with pgvector and full-text search.
- `lake.py`: Iceberg tables (`TABLES`), `open_catalog`, read and write helpers for each tier.
- `documents.py`: `register_document`, the upload step. Write-once raw files, automatic `supersedes`.
- `versioning.py`: `create_candidate`, `publish`, `reject`, `rollback`.
- `gate.py`: quality gate checks, `run_gate`, `record_sme_decision`.
- `lineage.py`: `trace_citation`, `sweep_superseded`.
- `retention.py`: `run_retention` for uploads, ops rows and Iceberg history.
- `factory.py`: `build_platform`, the only place that picks adapters.
- `testing.py`: `make_test_platform`, a full platform without Docker for tests in any lane.
- `migrate.py` and `migrations/`: Alembic migrations for Postgres.
- `cli.py`: the `chatbot-platform` command.

## Use it from another package

```python
from chatbot_platform.factory import build_platform

platform = build_platform()  # reads PLATFORM_* from the environment or .env
platform.registry.pending_doc_versions()
platform.index.search_dense(vector, version=platform.registry.get_alias("serving"), k=20)
```

In tests, never start Docker. Use the test platform:

```python
from chatbot_platform.testing import make_test_platform


def test_something(tmp_path):
    platform = make_test_platform(tmp_path)
```

## How a corpus version is built

1. `chatbot-platform upload` (or `register_document`) stores the file and registers a document version.
2. The pipeline reads `registry.pending_doc_versions()`, starts a run with `registry.start_run`, and runs W1 to W6. The workers write the Iceberg tiers with `lake.append_records` and `lake.write_chunk_set`.
3. `create_candidate(add=[...])` builds the next manifest from serving.
4. `run_gate` with a `GateContext` from `lake.read_clean_pages` and `lake.read_chunk_sets`.
5. When `report.requires_sme` is true, wait for `record_sme_decision`.
6. `publish(version_id, chunk_sets)` opens and closes validity intervals and moves the serving alias.

## Commands

```bash
uv run --package chatbot-platform chatbot-platform init
uv run --package chatbot-platform chatbot-platform upload book.pdf --course "STAT 101" --source-id "textbook ch1" --type textbook
uv run --package chatbot-platform chatbot-platform status
uv run --package chatbot-platform chatbot-platform rollback 3
uv run --package chatbot-platform chatbot-platform trace <chunk_id>
uv run --package chatbot-platform chatbot-platform sweep-lineage
uv run --package chatbot-platform chatbot-platform retention
```

`init` needs the `data` compose profile running (`uv run poe up-data`).

## Schema changes

- Registry and ops tables: edit `sql.py`, then create a revision:
  `uv run --package chatbot-platform alembic -c libs/platform/alembic.ini revision --autogenerate -m "short message"`.
  Remove the generated banner comments so the comment check passes.
- Serving tables: write the revision by hand. The vector dimension comes from `PLATFORM_EMBEDDING_DIM`.
- Iceberg tables: edit `lake.TABLES`. New columns must be optional. Renames need a migration job.
- Never edit a migration that has run anywhere. `0001_initial.py` creates the registry, serving and ops schemas, `0002_reporting.py` the reporting schema for dashboards.
- Views in `reporting` are written by hand in a migration. The monitoring dashboards read them, so run `uv run poe check-dashboards` after changing one.

## Test

```bash
uv run --package chatbot-platform pytest libs/platform/tests
```

The same suite runs on real Postgres with the `integration` marker. Start the `data` profile, then:

```bash
PLATFORM_TEST_DATABASE_URL=postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot_test uv run --package chatbot-platform pytest libs/platform/tests -m integration
```

The test database is wiped on every test. Never point it at a database you care about.
