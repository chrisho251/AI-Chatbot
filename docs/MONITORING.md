# Monitoring

**Version:** 1.0


## 1. How it fits together

- **Services** record metrics with `chatbot_common.metrics`. Every service built with `create_app` exposes them on `/metrics` and records the duration of every HTTP route automatically.
- **Prometheus** scrapes every service, the model servers, cAdvisor (containers) and the DCGM exporter (GPU) every 15 seconds. Config: `infra/local/prometheus/prometheus.yml`.
- **Postgres `reporting` schema** holds daily views over `ops` and `registry`, and the `ragas_summary` table. It is created by migration `0002_reporting.py`. Grafana reads it with the read-only `grafana_reader` role, which sees aggregates only, never rows about single students.
- **Grafana** loads the data sources and dashboards from the repo when it starts. Config: `infra/local/grafana/`.

## 2. Open the dashboards

```bash
docker compose --profile data --profile core --profile cpu --profile obs up -d
uv run poe init-platform
```

Then open http://localhost:3001. Locally, anonymous visitors are viewers. The admin login is `admin` / `admin` on first start.

The four dashboards are in the **AI-chatbot** folder:

- **Performance (Appendix B.1):** latency (time to first token), response time (end to end), throughput by level, output tokens per second, questions in flight, confidence, HTTP p95 and errors per service.
- **Safety and misuse (Appendix B.2):** guard detections by category, stage, action and detector, and blocked questions.
- **Resources (Appendix B.3):** CPU and memory per container, GPU utilization and memory, the model server queue, and which targets are up.
- **Quality and escalation (Appendix A.6 and C.2):** latest RAGAs scores and their trend, questions per day by level, escalation rate, external and expert response times, tool call verdicts, and corpus status.

Until a lane records its metrics, its panels stay empty. That is expected.

## 3. Who records what

Metric names are defined once in `libs/common/src/chatbot_common/metrics.py`.

- **`create_app` (automatic):** `chatbot_http_request_duration_seconds` for every route except `/health` and `/metrics`.
- **Gateway (Lane C):** `chatbot_first_token_seconds`, `chatbot_response_seconds`, `chatbot_requests_total` by level (`L1`, `L2`, `L3`, `blocked`), `chatbot_requests_in_flight`, `chatbot_guard_events_total` with stage `gateway`.
- **Orchestrator (Lane C):** `chatbot_confidence`, `chatbot_escalations_total` by stage (`external`, `expert`), `chatbot_external_response_seconds`.
- **W8 (Lane C):** `chatbot_output_tokens_total`, `chatbot_tool_calls_total`, `chatbot_tool_call_seconds`.
- **W5 (Lane B):** `chatbot_guard_events_total` with stage `w5_online` or `w5_ingest`.
- **Escalation service (Lane A):** `chatbot_expert_response_seconds`.
- **Eval runner (Lane D):** one row per run and metric in `reporting.ragas_summary`, next to `eval.ragas_scores`.
- **Services writing `ops` tables (Lanes A and C):** the daily `reporting` views read them, so nothing extra is needed.

Example, in the gateway:

```python
from chatbot_common.metrics import FIRST_TOKEN, REQUESTS

FIRST_TOKEN.observe(t_first_token - t0)
REQUESTS.labels(level="L1").inc()
```

## 4. Change a dashboard

1. Add the metric to `metrics.py` first, or the `reporting` object to a new migration.
2. Edit the dashboard in Grafana, then use **Export**, **Save to file**, and replace the JSON under `infra/local/grafana/dashboards/`. Keep the `uid`.
3. Run `uv run poe check-dashboards`. It fails when a panel uses an undefined `chatbot_` metric, a missing `reporting` object, or an unknown data source.
4. Open a PR. In CI, the Postgres job also runs every panel's SQL against a migrated database.

Rules:
- Aggregate in `reporting` views, not in panel SQL, so the queries are tested and reused.
- Never give Grafana access to `ops` or `registry` tables directly.
- Keep label values low cardinality: no request ids, user ids or free text in labels.

## 5. Maintenance

- **Weekly:** look at **Targets up** on the Resources dashboard. A target at 0 is a service down or a scrape config out of date.
- **After adding a service:** add it to `prometheus.yml` and to the compose `core` profile.
- **After a schema change:** if a `reporting` view reads a changed table, recreate the view in the same migration.
- **Before a milestone review:** export the four dashboards as PDF or PNG for the review period and write the performance summary from them (section 7).
- **Alerts (Lane D, M5):** add Grafana alert rules for latency p95, error rate, escalation rate, a target down, and disk space, provisioned as files like the dashboards.
- **Retention:** Prometheus keeps 15 days by default. Long-term history lives in Postgres and Iceberg, which the retention sweep manages.

## 6. Access for the Institution

- **Locally:** anonymous viewer access, for demos only.
- **On AWS (M5):** turn off anonymous access and sign in through Keycloak or Cognito with the `auditor` role. Give the Institution reviewers viewer rights on the AI-chatbot folder only.
- The `grafana_reader` password in `infra/local` is for local use only. On AWS it comes from Secrets Manager.

## 7. Milestone performance summary

Section 8 of the agreement asks for a written performance summary at each milestone review. From the dashboards, over the review period, report:

1. Latency and response time p50 and p95, against the Appendix D thresholds.
2. Throughput at 10 concurrent users, from the load test.
3. Guard detections by category and what was done about them.
4. CPU, memory and GPU peaks per worker and model server.
5. RAGAs scores against the targets, with the corpus and model versions.
6. Escalation rate, and external and expert response times.

## 8. Local troubleshooting

- **Quality panels say permission denied:** the Postgres volume predates the `grafana_reader` role, so migration 0002 skipped the grants. Either run `docker compose down -v` and start again (this deletes local data), or run these statements as the `chatbot` user: the `CREATE ROLE` line from `infra/local/postgres/init/01-databases.sql`, then `GRANT USAGE ON SCHEMA reporting TO grafana_reader`, `GRANT SELECT ON ALL TABLES IN SCHEMA reporting TO grafana_reader` and `ALTER DEFAULT PRIVILEGES IN SCHEMA reporting GRANT SELECT ON TABLES TO grafana_reader`.
- **cAdvisor panels empty on Windows or macOS:** Docker Desktop runs containers in a VM, and cAdvisor sees only part of it. The numbers are complete on Linux and on AWS.
- **GPU panels empty:** they need the `gpu` profile and an NVIDIA machine.
