# Local infrastructure

Configuration mounted by `compose.yaml`. Each folder belongs to one service. Profiles are described in [docs/TECH_STACK.md](../../docs/TECH_STACK.md), section 3.

**Owner:** Lane A, except `otel/`, `prometheus/`, `tempo/` and `grafana/`, which belong to Lane D.

- `postgres/init/`: runs once when the database volume is created. It adds the `dagster`, `keycloak` and `chatbot_test` databases, the pgvector extension, and the read-only `grafana_reader` role. To run it again: `docker compose down -v`, which deletes local data. Postgres is the only database of the platform, the platform migrations create every schema in `chatbot`.
- `seaweedfs/s3.json`: the S3 access key and secret. They must match `PLATFORM_S3_ACCESS_KEY` and `PLATFORM_S3_SECRET_KEY`.
- `traefik/dynamic.yml`: routes the public routes (`/v1/ask`, `/v1/answers/`, the expert answer route) to the api service and nothing else. Add mkcert certificates here for trusted local HTTPS.
- `keys/`: the local key file for pseudonyms and text encryption, mounted read-only into the api service. Git ignores it. Create it with the key script from the security lane (see the to-do list).
- `keycloak/chatbot-realm.json`: the `chatbot` realm with its seven roles and a public client. Add test users here.
- `searxng/settings.yml`: SearXNG with the JSON output that W7 reads.
- `dagster/`: the Dagster instance (Postgres storage) and the code location.
- `prometheus/prometheus.yml`: scrapes the api service, the model servers, cAdvisor and the GPU exporter. Compose keeps 90 days of metrics.
- `grafana/`: data sources, the dashboard provider, and the four dashboards in `grafana/dashboards/`. See [docs/MONITORING.md](../../docs/MONITORING.md).
- `otel/`, `tempo/`: traces and logs for the optional `traces` profile, for Lane D to complete.

## To do, Lane A

- Pin every image tag and digest in `compose.yaml`. `searxng` and `llama.cpp` still use moving tags.
- Write the script in `scripts/` that creates `keys/keys.json` for `chatbot_common.keys.FileKeyService`, and a command that drops an old key epoch.
- Add test users for each role to the Keycloak realm.
