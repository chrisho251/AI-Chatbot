# Changelog

**Read this when:** you need to know what changed in the design and in which files.
**Versions:** documents and packages move 1.0, 1.1 and so on to 1.9, then 2.0. Grafana dashboards keep their own whole-number version, which goes up by one with each change.

---

## 1.1 (2026-09-26)

Three architecture changes, and the smaller changes that follow from them:

1. **One api process for the online plane.** The gateway, orchestrator, escalation service and the online roles of W2 to W8 run in one FastAPI process and call each other as functions, through the same contracts. Only the W3 sandbox and the model servers stay in their own containers. Any component can move back to its own container with one setting.
2. **Postgres is the only database.** Apache Iceberg, the DuckDB query engine and the Glue and Athena plans are removed. The ingest tiers, operational history, evaluation and fine-tuning tables live in Postgres. Frozen datasets are write-once Parquet exports.
3. **Keys without Vault.** A `KeyService` port reads a local key file, and KMS replaces it on AWS.

Also: conversation memory for follow-up questions, a time-per-worker metric, optional `traces` and `finetune` compose profiles, 90 days of Prometheus retention, a Locust load test, and a model plan for M1.

### Documentation

- `docs/architecture/ARCHITECTURE.md` (1.0 → 1.1): the api service, principles for one package per worker, one online process and one database, the Postgres storage layout and tiers, retention in place, conversation steps and the parallel guard in the query path, new contracts, new failure modes, updated repository map.
- `docs/TECH_STACK.md` (1.0 → 1.1): compose profiles (`core`, `traces`, `finetune`, no `images`), 22 services instead of 33, Postgres only with a "Why not Iceberg" note, the api service, keys without Vault, the M1 model plan (generator size, judge family, guard size), Locust, the AWS mapping without catalog and query engine, TEI in the `gpu` profile.
- `docs/MONITORING.md` (1.0 → 1.1): one metrics target, `chatbot_worker_call_seconds`, the optional traces profile, 90 days in Prometheus, where resources per worker come from.
- `docs/architecture/diagrams/01-system-architecture.*`, `02-worker-map.*`, `03-rag-pipeline.*`, `04-ingestion.*` (JSON source, HTML and PNG): the online plane as one api process, keys instead of Vault, the ingest tables in Postgres instead of Iceberg, one package with two entrypoints.
- `docs/CHANGELOG.md` (new): this file.
- `README.md`: the api service, Postgres as the only database, the changelog link, the `tests/` folder.

### Online plane: one api process

- `services/api/` (new package `chatbot-api` 1.1.0): `serve.py` mounts the public routes and registers every contract endpoint as a local handler, `CHATBOT_<SERVICE>_URL` moves a component out. Tests and README.
- `libs/common/src/chatbot_common/http.py`: `ContractClient` calls local handlers as functions, `register_local` and `shared_client`, time of every call recorded.
- `libs/common/src/chatbot_common/service.py`: `add_contract_routes` serves the same handlers over HTTP.
- `libs/common/src/chatbot_common/metrics.py`: new metric `chatbot_worker_call_seconds`.
- `libs/common/src/chatbot_common/settings.py`: `service_url` only for components in their own container, new settings `key_file` and `otel_endpoint`.
- `libs/common/src/chatbot_common/telemetry.py`: traces are off without the `traces` profile, spans around local calls.
- `libs/common/tests/test_common.py`, `libs/common/README.md`: local handlers and contract routes.
- `libs/contracts/src/chatbot_contracts/routes.py`, `escalation.py`: new record `TicketQuery` and endpoint `GET_TICKET`, so the gateway reads late answers through a contract.
- `libs/contracts/src/chatbot_contracts/base.py`: `SCHEMA_VERSION` 1.0 → 1.1.
- `libs/contracts/src/chatbot_contracts/samples.py`, `libs/contracts/tests/test_samples.py`, `libs/contracts/README.md`, `libs/contracts/schemas/*.json` (regenerated for schema version 1.1, new `TicketQuery.json`).
- `services/gateway/src/chatbot_gateway/serve.py`: public routes in a `router`, optional `conversation_id` form field.
- `services/gateway/src/chatbot_gateway/ask.py`, `guard.py`, `limits.py`: guard runs next to the answer and the gateway holds events until the verdict, calls through `shared_client`.
- `services/orchestrator/src/chatbot_orchestrator/serve.py`, `services/escalation/src/chatbot_escalation/serve.py`: `HANDLERS` plus `add_contract_routes`, the expert route in a `router`.
- `services/orchestrator/src/chatbot_orchestrator/pipeline.py`, `groundedness.py`: calls through `shared_client`, CPU work in worker threads.
- `workers/w2_vision` to `workers/w8_gen`, `serve.py` in each: `HANDLERS` plus `add_contract_routes`. W4 runs its check in a worker thread.
- `workers/w2_vision/.../photo.py`, `workers/w3_code/.../runner.py`, `workers/w5_clean/.../injection.py`, `workers/w8_gen/.../tools.py`: notes for running inside the api process.
- Worker and service tests: each checks that `HANDLERS` covers every endpoint of its component.
- `scripts/check_boundaries.py`, `tests/tooling/test_scripts.py`: only `chatbot-api` may depend on services and workers, and nothing may depend on it.
- `pipelines/src/chatbot_pipelines/steps.py`, `tests/test_smoke.py`, `README.md`: every offline step runs in its own container from the app image.
- Worker `job.py` files: Dagster starts them from the app image.
- Worker and service READMEs: how each component runs inside the api service.

### Data platform: Postgres only

- `libs/platform/src/chatbot_platform/sql.py`: new schemas `ingest`, `eval`, `ft`, new tables `ops.conversations`, `ops.request_facts`, `ops.guard_events`, the ingest tiers, eval and fine-tuning tables.
- `libs/platform/src/chatbot_platform/ingest.py` (new): the cleaned and chunked tiers in Postgres, safe to write twice.
- `libs/platform/src/chatbot_platform/exports.py` (new): write-once Parquet exports in the `exports` bucket.
- `libs/platform/src/chatbot_platform/migrations/versions/0003_postgres_platform.py` (new): creates the new schemas and tables, drops the old Iceberg catalog tables.
- `libs/platform/src/chatbot_platform/migrations/env.py`: autogenerate covers every schema except serving.
- `libs/platform/src/chatbot_platform/retention.py`: rules in place, uploads, blanked text after 365 days, ops rows after 730 days, staged chunks after 90 days.
- `libs/platform/src/chatbot_platform/settings.py`: `exports` bucket instead of `warehouse`, new retention settings, no catalog settings.
- `libs/platform/src/chatbot_platform/factory.py`, `testing.py`, `cli.py`, `registry.py`: no catalog, `init` migrates and creates buckets only.
- `libs/platform/tests/test_ingest.py`, `test_exports.py` (new), `test_retention.py` (rewritten).
- `libs/platform/pyproject.toml`: `pyiceberg` removed. `README.md` updated.
- `pipelines/src/chatbot_pipelines/schedules.py`, `ingestion.py`, `README.md`: no hourly copy job, the gate reads from `chatbot_platform.ingest`.
- Worker `job.py` files and READMEs of W1 to W6, `workers/w5_clean/.../dedupe.py`, `workers/w6_embed/README.md`: write the `ingest` tables.
- `ml/eval/src/chatbot_eval/golden_set.py`, `ragas_runner.py`, `README.md`: results in the Postgres `eval` tables, Parquet export of item scores, judge from another model family, golden items sent through the gateway.
- `ml/finetune/src/chatbot_finetune/dataset.py`, `README.md`: dataset versions frozen as Parquet exports, fine-tuning is an optional later phase.

### Keys without Vault

- `libs/common/src/chatbot_common/keys.py` (new): the `KeyService` port and the `FileKeyService` stub.
- `services/gateway/src/chatbot_gateway/pseudonym.py`, `settings.py`: pseudonyms through the key service, Vault settings removed.
- `services/gateway/pyproject.toml`: `hvac` removed.
- `services/escalation/src/chatbot_escalation/tickets.py`, `services/orchestrator/src/chatbot_orchestrator/interactions.py`: text encrypted with the key service.

### Conversation memory

- `libs/contracts/src/chatbot_contracts/query.py`: `AskRequest.conversation_id`, new record `Turn`, `GenerationRequest.history`.
- `libs/contracts/src/chatbot_contracts/escalation.py`: `StreamEvent.conversation_id`.
- `services/orchestrator/src/chatbot_orchestrator/conversation.py` (new): history and standalone question.
- `services/orchestrator/src/chatbot_orchestrator/settings.py`: `history_turns`.
- `workers/w8_gen/src/chatbot_w8_gen/prompt.py`: earlier turns in the prompt.

### Infrastructure

- `compose.yaml`: one `api` service replaces the gateway, orchestrator, escalation, W2 to W8 and the `images` profile. Vault removed. `traces` and `finetune` profiles, Prometheus keeps 90 days, TEI also runs with `gpu`, the key file is mounted into the api service.
- `.env.example`, `.gitignore`: key file and trace settings, Vault and warehouse settings removed, `infra/local/keys/` ignored.
- `infra/local/prometheus/prometheus.yml`: one scrape target for the online plane.
- `infra/local/traefik/dynamic.yml`: only the public routes reach the api service.
- `infra/local/grafana/dashboards/performance.json` (version 1 → 2): new panel "Time per worker, p95".
- `infra/local/grafana/dashboards/resources.json`, `safety.json` (version 1 → 2): descriptions for one api container and `ops.guard_events`.
- `infra/local/grafana/provisioning/datasources/datasources.yml`: Loki and Tempo need the traces profile.
- `infra/local/README.md`, `infra/aws/terraform/README.md`: the key file, one app image, no catalog.

### Tooling and tests

- `tests/load/locustfile.py` (new), `tests/README.md`: load test for 10 concurrent students.
- `uv.lock`: regenerated. Adds `chatbot-api`, removes `pyiceberg`, `mmh3`, `pyroaring`, `strictyaml` and `hvac`.
- `pyproject.toml` of every package: version 1.0.0 → 1.1.0.

### Removed

- `libs/platform/src/chatbot_platform/lake.py`, `aws.py`, `query_engine.py`, `libs/platform/tests/test_lake.py`: the Iceberg lake, the Glue catalog stub and the DuckDB query engine stub.
- `pipelines/src/chatbot_pipelines/snapshots.py`: the hourly copy into Iceberg history.
