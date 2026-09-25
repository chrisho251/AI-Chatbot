# Local infrastructure

Configuration mounted by `compose.yaml`. Each folder belongs to one service. Profiles are described in [docs/TECH_STACK.md](../../docs/TECH_STACK.md), section 3.

**Owner:** Lane A, except `otel/`, `prometheus/`, `tempo/` and `grafana/`, which belong to Lane D.

- `postgres/init/`: runs once when the database volume is created. It adds the `dagster`, `keycloak` and `chatbot_test` databases, the pgvector extension, and the read-only `grafana_reader` role. To run it again: `docker compose down -v`, which deletes local data.
- `seaweedfs/s3.json`: the S3 access key and secret. They must match `PLATFORM_S3_ACCESS_KEY` and `PLATFORM_S3_SECRET_KEY`.
- `traefik/dynamic.yml`: routes `http://localhost` to the gateway. Add mkcert certificates here for trusted local HTTPS.
- `keycloak/chatbot-realm.json`: the `chatbot` realm with its seven roles and a public client. Add test users here.
- `searxng/settings.yml`: SearXNG with the JSON output that W7 reads.
- `dagster/`: the Dagster instance (Postgres storage) and the code location.
- `prometheus/prometheus.yml`: scrapes every service, the model servers, cAdvisor and the GPU exporter.
- `grafana/`: data sources, the dashboard provider, and the four dashboards in `grafana/dashboards/`. See [docs/MONITORING.md](../../docs/MONITORING.md).
- `otel/`, `tempo/`: traces, for Lane D to complete.

## To do, Lane A

- Pin every image tag and digest in `compose.yaml`. `searxng` and `llama.cpp` still use moving tags.
- Create the Vault Transit key used by the gateway for pseudonyms, with a small script in `scripts/`.
- Add test users for each role to the Keycloak realm.
