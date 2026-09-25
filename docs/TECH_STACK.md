# Tech stack

**Version:** 1.0
**Date:** 2026-09-25
**Read this when:** you set up a machine, add a dependency, or need to know what a component is for.
**Not in this file:** how the components work together. That is in [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md).

This file is the inventory of the project: every service, database, model, library and tool, what it is for, and whether it runs on any team member's machine.

---

## 1. Portability rules

The stack must run on any team member's machine, not only on one laptop.

1. **Everything runs in containers.** Docker Compose starts every service. The host needs only Docker, Git and uv.
2. **One Python toolchain.** uv installs the pinned Python version (`.python-version`) and the locked packages (`uv.lock`). Nobody installs Python packages globally.
3. **Pinned versions.** Images are pinned by tag in `compose.yaml` (by digest at release). Packages are pinned in `uv.lock`. Models are pinned by repository and revision in `.env`.
4. **Multi-architecture images.** Every image in the default profiles runs on `linux/amd64` (Intel, AMD) and `linux/arm64` (Apple Silicon, ARM laptops). Anything that needs NVIDIA hardware lives only in the `gpu` profile.
5. **CPU by default, GPU optional.** The default profiles run on CPU. A machine with an NVIDIA GPU adds the `gpu` profile. A Mac can run the LLM natively (llama.cpp or Ollama with Metal) and point `LLM_BASE_URL` at it.
6. **No host-specific paths or scripts.** Paths are relative to the repo. Tasks run through `uv run poe <task>`, which is Python, not Bash or PowerShell. `.gitattributes` forces LF line endings so containers behave the same on Windows.
7. **Every endpoint is configuration.** Model URLs, storage endpoints and credentials come from `.env` (template in `.env.example`). A component can move between a container, the host and AWS without code changes.
8. **Tests do not need the full stack.** Unit tests use in-memory and local-filesystem adapters. Integration tests start only the `data` profile.

---

## 2. What a machine needs

### Host tools

- **Docker Desktop or Docker Engine, with Compose v2** (Engine 27+, Compose 2.30+): runs every service.
  Windows: Docker Desktop with the WSL2 backend. macOS: Docker Desktop, OrbStack or Colima. Linux: Docker Engine.
- **Git** (2.40+): source control.
- **uv** (0.5+): installs Python 3.12 and all packages, runs tasks.
- **mkcert** (optional, 1.4+): trusted local TLS certificates for Traefik.
- **NVIDIA driver 550+ and NVIDIA Container Toolkit** (optional): only for the `gpu` profile. Linux, or Windows through WSL2. Not available on macOS.

### Machine sizing (approximate)

- **`data` profile only** (data platform work and tests): 4 GB RAM, 5 GB free disk.
- **`data` + `core` + `cpu`** (full answer path on CPU): 16 GB RAM, 40 GB disk. The 4B model runs in 4-bit weights. Slow, but fine for development.
- **All profiles on CPU:** 24 to 32 GB RAM, 60 GB disk. Adds Dagster, Docling, the observability stack and the R sandbox.
- **`gpu` profile** (target for 10 concurrent users): 32 GB+ RAM, 200 GB disk, one NVIDIA GPU with 24 GB VRAM (16 GB works with 4-bit weights).

---

## 3. Compose profiles

Start only what the task needs, for example `docker compose --profile data up`.

- **`data`:** Postgres + pgvector, SeaweedFS, bucket and schema bootstrap. Enough for data platform work and integration tests.
- **`core`:** Traefik, Keycloak, Vault, gateway, orchestrator, escalation, online workers W2 to W8. The answer path.
- **`cpu`:** llama.cpp server, TEI (amd64). Models on any machine.
- **`gpu`:** vLLM, TEI GPU, DCGM exporter. Needed for 10 concurrent users.
- **`search`:** SearXNG. W7 external search.
- **`sandbox`:** W3 code sandbox. W3 execution.
- **`pipeline`:** Dagster webserver and daemon, MLflow. The offline plane.
- **`obs`:** OTel Collector, Prometheus, Loki, Tempo, Grafana, cAdvisor. Monitoring for Appendix B.
- **`dev`:** Mailpit. Captures local email.
- **`images`:** builds offline-only worker images (W1) that Dagster starts. Never run directly.

Common combinations:
- Data platform work: `data`
- Answer path on CPU: `data core cpu search sandbox dev`
- Load test: every profile, with `gpu` instead of `cpu`

---

## 4. Databases and storage

- **PostgreSQL 16 + pgvector:** serving index (dense vectors and full-text), corpus registry, lineage and hot operational tables. Also hosts the Iceberg SQL catalog and the Dagster, MLflow and Keycloak databases.
  Image `pgvector/pgvector:pg16`. Runs on amd64 and arm64. PostgreSQL licence.
- **SeaweedFS (S3 API):** local object store for the `raw`, `uploads`, `external`, `warehouse` (Iceberg data) and `mlflow` buckets. Replaces MinIO, see the note below.
  Image `chrislusf/seaweedfs`. Runs on amd64 and arm64. Apache-2.0.
- **Apache Iceberg (PyIceberg):** table format for the `cleaned` and `chunked` tiers and every history table. Snapshots give time travel and reproducible datasets.
  Python package `pyiceberg`. Apache-2.0.
- **DuckDB:** local analytics queries over Iceberg tables (quality gate checks, reports, lineage sweeps).
  Python package `duckdb`. MIT.
- **Local filesystem adapter:** zero-dependency object store and warehouse for unit tests and quick experiments. Part of `libs/platform`.

**Why not MinIO.** MinIO stopped publishing community Docker images in October 2025, put the community edition in maintenance mode in December 2025 and archived the repository in 2026. New machines cannot pull a current image and there are no security fixes. The platform talks to storage only through the S3-compatible `ObjectStore` port, so SeaweedFS drops in locally and S3 stays the cloud target. Other options are Garage (AGPL-3.0) and RustFS (Apache-2.0, still alpha).

---

## 5. Platform services (containers)

Every image below runs on amd64 and arm64 unless it says otherwise.

- **Traefik** (profile `core`): TLS at the edge, routes HTTPS to the gateway and admin UIs.
  Image `traefik`. MIT.
- **Keycloak** (profile `core`): OIDC identity provider and RBAC roles `student`, `sme`, `expert`, `data_engineer`, `ml_engineer`, `ops`, `auditor`.
  Image `quay.io/keycloak/keycloak`. Apache-2.0.
- **HashiCorp Vault** (profile `core`): pseudonymization keys (HMAC), Transit envelope encryption for student free text, secrets.
  Image `hashicorp/vault`. BUSL-1.1. OpenBao (MPL-2.0) is an API-compatible alternative.
- **SearXNG** (profile `search`): self-hosted meta search engine that W7 uses for external web search. No API key, no per-query cost.
  Image `searxng/searxng`. AGPL-3.0.
- **W3 code sandbox** (profile `sandbox`): isolated runner for R, Python and Excel formula checks. No network, with CPU, memory and time limits.
  Built from `rocker/r-ver` plus Python. Project code. R itself is GPL-2/3.
- **Dagster webserver and daemon** (profile `pipeline`): runs the offline plane. Sensors for new files, schedules for enrichment, RAGAs, retention and metric snapshots, jobs for fine-tuning.
  Built from `python:3.12-slim`. Apache-2.0.
- **MLflow** (profile `pipeline`): model registry and experiment tracking for fine-tuned adapters. Artifacts go to the object store.
  Built from `python:3.12-slim`. Apache-2.0.
- **Mailpit** (profile `dev`): captures outgoing email locally (expert notifications, gate reports).
  Image `axllent/mailpit`. MIT.
- **OpenTelemetry Collector** (profile `obs`): receives traces, metrics and logs from every service.
  Image `otel/opentelemetry-collector-contrib`. Apache-2.0.
- **Prometheus** (profile `obs`): real-time metrics store and alert rules.
  Image `prom/prometheus`. Apache-2.0.
- **Loki** (profile `obs`): log store.
  Image `grafana/loki`. AGPL-3.0.
- **Tempo** (profile `obs`): trace store.
  Image `grafana/tempo`. AGPL-3.0.
- **Grafana** (profile `obs`): the monitoring dashboards for Appendix B and C.2, over Prometheus and the Postgres `reporting` schema. Dashboards are JSON files in the repo, see [MONITORING.md](MONITORING.md).
  Image `grafana/grafana`. AGPL-3.0.
- **cAdvisor** (profile `obs`): CPU and memory per container, for every worker and model server. Gives partial data under Docker Desktop.
  Image `gcr.io/cadvisor/cadvisor`. Apache-2.0.
- **NVIDIA DCGM exporter** (profile `gpu`): GPU memory and utilization.
  Image `nvcr.io/nvidia/k8s/dcgm-exporter`. amd64 with NVIDIA only. Apache-2.0.

---

## 6. Model serving

All inference is self-hosted with open-weight models. There is no paid inference API and no per-token cost (Appendix A.2).

- **llama.cpp server** (profile `cpu`): LLM, judge and vision-language model on CPU, with an OpenAI-compatible API and GGUF weights.
  Image `ghcr.io/ggml-org/llama.cpp:server`. amd64 and arm64. MIT.
- **vLLM** (profile `gpu`): LLM, LoRA adapters, judge and vision-language model on GPU. Continuous batching handles 10+ concurrent streams.
  Image `vllm/vllm-openai`. amd64 with NVIDIA only. Apache-2.0.
- **Text Embeddings Inference, TEI** (profiles `cpu` and `gpu`): embeddings and reranking over HTTP.
  Image `ghcr.io/huggingface/text-embeddings-inference`. amd64 only, no prebuilt arm64 image. Apache-2.0.
- **In-process adapter (sentence-transformers):** portable fallback for embeddings and reranking inside W6 and W7. Used on arm64 machines and in tests.
  Python package. Apache-2.0.
- **Ollama** (optional, outside Docker): convenience runner for the LLM on a Mac with Metal acceleration.
  Host install. MIT.

### Default models

Pin exact revisions in `.env`. Review newer open-weight releases at M1 and record any change here.

- **Generation and fine-tuning base:** Qwen3 4B-class instruct. Used by W8 and by W3 for code generation. Apache-2.0.
- **RAGAs judge:** the same family at 8B, run off-peak. Used by the eval runner. Apache-2.0.
- **Embeddings:** BAAI bge-m3. Used by W6. MIT.
- **Reranker:** BAAI bge-reranker-v2-m3. Used by W7. Apache-2.0.
- **Vision-language** (student photos, handwritten formulas, charts): IBM Granite Vision class, with SmolVLM class as the lighter option. Used by W2. Apache-2.0.
- **Layout, OCR, formula and code extraction for PDFs:** Docling with its layout and code/formula models. Used by W1, W2, W4. MIT.
- **Prompt-injection guard:** ProtectAI deberta-v3-base prompt-injection v2. Used by the gateway and W5. Apache-2.0.
- **Misuse and safety guard:** IBM Granite Guardian. Used by the gateway. Apache-2.0.
- **Groundedness for confidence:** NLI cross-encoder, DeBERTa-v3 MNLI class. Used by the orchestrator. Apache-2.0.
- **PII detection:** Microsoft Presidio with a spaCy English model. Used by W5. MIT.

---

## 7. External sources

These are free and need no paid API key. W7 uses them only after internal retrieval is not enough, and the offline enrichment job uses them on a schedule. Queries leave PII-stripped. Only allowlisted domains are fetched, `robots.txt` is respected and every result records its licence.

- **SearXNG** (self-hosted): general web search restricted to the allowlist. No limit of its own, but upstream engines may throttle.
- **NCBI E-utilities (PubMed):** biomedical literature over REST. 3 requests per second without a key, 10 with a free key.
- **Europe PMC REST API:** open-access full text. Fair use.
- **MedlinePlus web service:** consumer health topics. Fair use.
- **OpenStax and LibreTexts** (through SearXNG with a site filter): open textbooks with exercises and answer keys. Licence per page, usually CC BY or CC BY-NC-SA.

---

## 8. Python libraries by package

- **`libs/contracts`:** Pydantic v2. Typed, versioned records between workers, with JSON Schema export.
- **`libs/platform`:** PyIceberg, PyArrow, SQLAlchemy 2, psycopg 3, Alembic, pgvector-python, boto3, pydantic-settings. Data platform ports and adapters, migrations, versioning, lineage. DuckDB joins when the analytics query engine is built.
- **`libs/common`:** FastAPI, Uvicorn, httpx, pydantic-settings, prometheus-client. App factory with a metrics route, the metric catalogue, contract client, test fakes, LLM and TEI clients. Lane D adds the OpenTelemetry SDK for tracing.
- **`services/gateway`:** FastAPI, Uvicorn, sse-starlette, Authlib, hvac, transformers. Auth, RBAC, rate limit, pseudonymization, guard, SSE streaming, uploads.
- **`services/orchestrator`:** FastAPI, httpx, sentence-transformers (NLI). Request pipeline, citation validation, confidence and level routing.
- **`services/escalation`:** FastAPI, SQLAlchemy. Tickets, on-duty rota, notifications, expert answer API.
- **`workers/w1_ingest`:** Docling. Layout analysis, region split, document version registration.
- **`workers/w2_vision`:** Docling OCR and an OpenAI-compatible client for the vision-language model. OCR, captions, reading student photos.
- **`workers/w3_code`:** openpyxl, formulas, numpy, pandas, scipy, statsmodels, and R inside the sandbox. Generate, run and check R, Python and Excel solutions.
- **`workers/w4_math`:** SymPy, SciPy, statsmodels. Normalize LaTeX, compute and verify statistics and dosages.
- **`workers/w5_clean`:** Presidio, datasketch (MinHash), ftfy, trafilatura. Normalize, dedupe, PII scrub, injection scan, clean web pages.
- **`workers/w6_embed`:** sentence-transformers or a TEI client, and a transformers tokenizer. Structure-aware chunking with token counts, embeddings for content and queries.
- **`workers/w7_deepsearch`:** httpx, trafilatura, SQLAlchemy. Internal hybrid search and rerank, external search fallback, enrichment.
- **`workers/w8_gen`:** an OpenAI-compatible client, Jinja2. Grounded prompts, streaming, tool calls to W3 and W4, citations.
- **`pipelines`:** Dagster, dagster-docker, dagster-postgres, dagster-webserver. Sensors, schedules and jobs. Each worker step runs in its own image through Dagster Pipes.
- **`ml/eval`:** ragas, datasets. RAGAs on the golden set and sampled live traffic.
- **`ml/finetune`:** transformers, PEFT, TRL, bitsandbytes, MLflow. Dataset build, QLoRA training, registry. Training needs an NVIDIA GPU.

---

## 9. Development and test tools

- **uv (workspace mode):** Python version, dependency lock, virtual environments. MIT or Apache-2.0.
- **Ruff:** linting and formatting. MIT.
- **mypy:** static type checks. MIT.
- **pytest and pytest-cov:** unit and integration tests, coverage. MIT.
- **moto:** fakes the S3 API in unit tests of the object store. Apache-2.0.
- **poethepoet:** cross-platform task runner, for example `uv run poe test` or `uv run poe up`. MIT.
- **pre-commit:** runs Ruff, mypy and file checks before each commit. MIT.

---

## 10. From local to AWS (phase 2)

Each line reads: concern, then local choice → AWS choice, then the port (interface) the code talks to.

- **Object store:** SeaweedFS → S3. Port `ObjectStore`.
- **Table catalog:** Iceberg SQL catalog in Postgres → AWS Glue Data Catalog. Port `TableCatalog`.
- **Analytics queries:** DuckDB → Athena. Port `QueryEngine`.
- **Serving index and lineage:** PostgreSQL + pgvector → RDS PostgreSQL + pgvector. Ports `VectorIndex` and `LineageStore`.
- **Orchestration:** Dagster OSS → Dagster on ECS. Code: Dagster definitions.
- **LLM, VLM, embeddings:** llama.cpp and TEI → vLLM and TEI on an EC2 GPU host. Ports: OpenAI-compatible HTTP, `Embedder`, `Reranker`.
- **External search:** SearXNG container → SearXNG on ECS. Port `WebSearch`.
- **Code sandbox:** sandbox container on an internal network → ECS task with no egress. Port `CodeRunner`.
- **Identity:** Keycloak → Cognito. Protocol OIDC.
- **Keys and secrets:** Vault → KMS + Secrets Manager. Ports `KeyService` and `Secrets`.
- **TLS:** Traefik + mkcert → ALB + ACM. No port needed.
- **Email:** Mailpit → SES. Port `Notifier`.
- **Observability:** OTel Collector, Prometheus, Loki, Tempo, Grafana → CloudWatch or Amazon Managed Prometheus and Grafana. Protocol OpenTelemetry.
- **Model registry:** MLflow + object store → MLflow + S3. MLflow API.
- **Container images:** local build → ECR.
- **Infrastructure as code:** `compose.yaml` with profiles → Terraform modules (OpenTofu compatible).

GPU instances are not free-tier eligible. See section 11 for cost and the low-cost plan for the test phase.

---

## 11. Cost

Checked on 2026-09-25. Prices change, so check the provider pages before you rely on a number.

### Development on team machines: no cost

- **Software.** Everything in this file is free to use. AGPL components (Grafana, Loki, Tempo, SearXNG) only create obligations when you modify them and offer them over a network. We run the published images unchanged. BUSL components (Vault, Terraform) are free for this use. OpenBao and OpenTofu are drop-in open source alternatives.
- **Models.** Every default model is open weight under Apache-2.0 or MIT. Downloads from Hugging Face are free. A free Hugging Face token avoids anonymous rate limits.
- **External sources.** SearXNG, PubMed, Europe PMC and MedlinePlus are free. A free NCBI key raises the PubMed limit from 3 to 10 requests per second.
- **Docker Desktop.** Free for personal use, students, education and small businesses. On computers owned by an organization with more than 250 employees it needs a paid subscription. Rancher Desktop or Docker Engine in WSL2 are free alternatives.
- **Docker Hub.** No cost. Anonymous pulls are rate limited, so log in with a free account if a pull is refused.
- **Fine-tuning.** QLoRA on a 4B model needs an NVIDIA GPU. Kaggle notebooks and Google Colab give free GPU time (T4 16 GB), which is enough for the first checkpoints.

### Continuous integration: no cost, with a limit

- A private GitHub repository includes 2,000 Linux minutes per month. With the default spending limit of zero, GitHub stops running workflows when the minutes run out. It does not charge.
- CI therefore tests only the packages a change touches (`scripts/changed_packages.py`), caches uv downloads, and cancels a run when a newer push arrives. Documentation-only changes run no package tests.
- If minutes still run out: GitHub Education gives student accounts 3,000 minutes, and a team machine can serve as a self-hosted runner, which is free.

### Testing on AWS (M5 and M6): this costs money

- About the AWS 12-month free tier, accounts created on or after 15 July 2025 no longer get it. They get 100 to 200 USD of credits for 6 months on the Free plan. Accounts created before that date keep the legacy 12-month free tier.
- No GPU instance is free-tier eligible, and the 10-user target needs a GPU. Using one requires the Paid plan. Credits left over still apply after the upgrade.
- Approximate on-demand prices in us-east-1: g4dn.xlarge (T4) about 0.53 USD per hour, g6.xlarge (L4 24 GB) about 0.80 USD per hour, g5.xlarge (A10G 24 GB) about 1.00 USD per hour. ca-central-1 is slightly more expensive.
- Common hidden costs: a NAT Gateway (about 33 USD per month even when idle), public IPv4 addresses (about 3.60 USD per month each), a load balancer (from about 16 USD per month), CloudWatch log ingestion, and data transfer out.

### Low-cost plan for the AWS test phase

1. One EC2 GPU instance runs the same `compose.yaml` with the `gpu` profile. No ECS, no NAT Gateway, no load balancer during testing. Traefik gets a free TLS certificate from Let's Encrypt.
2. Start the instance only for test sessions and stop it afterwards. Stopped instances only pay for their disk.
3. Keep data on the instance disk and in S3. Take an EBS snapshot before each milestone review.
4. Set an AWS Budget with an email alert from day one.
5. Rough order of magnitude: 60 hours of GPU testing costs 50 to 60 USD, plus about 16 USD per month for a 200 GB disk. Most of it fits in the new-account credits.
