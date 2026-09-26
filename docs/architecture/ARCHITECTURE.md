# AI-chatbot: backend architecture

**Version:** 1.1 (local first)
**Date:** 2026-09-26
**Scope:** backend only. The student frontend already exists and lives outside this repo.
**Read this when:** you need to know how the system works: which component does what, how data moves, how versions, security and failures are handled.
**Not in this file:** product names, versions, licences and machine setup. Those are in [../TECH_STACK.md](../TECH_STACK.md).

**Related documents**
- [../TECH_STACK.md](../TECH_STACK.md): every service, tool, model and database, with portability notes and compose profiles.
- [../MONITORING.md](../MONITORING.md): metrics, dashboards and how to maintain them.
- [../CHANGELOG.md](../CHANGELOG.md): what changed in each version of this design.

**Diagrams** (drawn with Archify; each HTML is interactive, with a PNG and its JSON source next to it in [diagrams/](diagrams/))
- [01 System architecture](diagrams/01-system-architecture.html): the whole system on one page, grouped by plane, with code paths.
- [02 Worker map](diagrams/02-worker-map.html): the eight workers in their offline and online roles, and the contracts between them.
- [03 RAG pipeline](diagrams/03-rag-pipeline.html): one student question to a cited answer, an external-source answer, or an expert escalation.
- [04 Ingestion](diagrams/04-ingestion.html): how an uploaded PDF or an external exercise becomes a published knowledge base version.

**Deployment stance.** Phase 1 runs everything as containers on any team machine with Docker Compose. Phase 2 moves to AWS. Every infrastructure dependency sits behind a port (an interface), so the move swaps adapters and infrastructure code, not application logic.

---

## 1. Design principles

1. **Two planes, one platform.** The *online plane* answers students and is bound by latency. The *offline plane* builds the knowledge base and is bound by throughput. They share the data platform and model serving.
2. **One worker, one package, two entrypoints.** Each of the eight workers is its own package with its own contracts, tests and lane owner. Online, a worker is a set of local handlers that run inside the api process. Offline, the same package runs as a Dagster step in its own container. Both roles share code, metric labels and a contract boundary.
3. **One online process.** The gateway, the orchestrator, the escalation service and the online roles of W2 to W8 run in one FastAPI process, the api service. They call each other through contracts as plain function calls. Heavy computation stays in the model servers, and generated code stays in the sandbox. Any component can move to its own container with one setting, without code changes.
4. **Internal first, external second.** Answers come from the vetted knowledge base. The external web is a fallback, always labelled "unvetted external source", and never enters the knowledge base without the quality gate and SME sign-off.
5. **The knowledge base is immutable and versioned.** A corrected document becomes a new document version, which becomes a new knowledge base version. Serving points at a version through an alias, so rollback means moving the alias.
6. **Contracts, not shared tables.** Workers exchange typed, versioned records. No worker reads another worker's storage.
7. **One database.** Postgres holds every table of the platform: registry, serving index, ingest tiers, operational data, evaluation and reporting. The object store holds files only.
8. **Ports and adapters for all infrastructure.** Object store, index, lineage, identity, keys, secrets, mail, web search, code runner and metrics are interfaces with a local adapter and an AWS adapter.
9. **Operational data is platform data.** RAGAs scores, latency, throughput, guard events, escalations and tool calls land as Postgres tables with history. Resource use stays in Prometheus for 90 days.
10. **Privacy by construction.** Student identity is pseudonymized at the gateway. Nothing downstream sees a real student ID. Outbound external queries are PII-stripped.
11. **Portable by default.** CPU and multi-architecture images by default, GPU as an optional profile, every endpoint in configuration.

---

## 2. Components and responsibilities

Worker names follow Appendix A.4: W1 Worker-ingest, W2 Worker-vision, W3 Worker-code, W4 Worker-math, W5 Worker-clean, W6 Worker-embed, W7 Worker-deepsearch, W8 Worker-gen.

Each entry reads: **component** (plane, code folder): what it does.

### The api service

- **API service** (online, `services/api`): one FastAPI process for the whole online plane. It mounts the public routes of the gateway and of the escalation service, and registers every contract endpoint of the orchestrator, the escalation service and W2 to W8 as a local handler. `ContractClient` calls a local handler as a function, with the same request and response records as over HTTP, and records the time of every call per worker. The internal endpoints are not exposed over HTTP. Setting `CHATBOT_<SERVICE>_URL` moves that component to its own container, where it runs its standalone app from the same image.

### Online components (inside the api service)

- **API gateway** (online, `services/gateway`): validates OIDC tokens, enforces RBAC, rate limits and admission control. Pseudonymizes the student. Starts or continues a conversation. Runs the prompt-injection and misuse guards next to input preparation and holds the answer until their verdict. Accepts attachments into `uploads`. Streams answers and status events over SSE. Records `t0`, `t_first_token` and `t_last_byte`.
- **Query orchestrator** (online, `services/orchestrator`): pins the `serving` knowledge base version per request. Reads the conversation history and rewrites a follow-up into a standalone question. Runs input preparation (W2, W5, W6), retrieval (W7), generation (W8), citation validation and confidence scoring. Routes L1, L2 or L3 and logs the interaction.
- **Escalation service** (online, async, `services/escalation`): owns escalation tickets, the on-duty expert rota, expert notifications and the expert answer API. Delivers late expert answers to the student.

### The eight workers

- **W1 ingest** (offline, `workers/w1_ingest`): registers a document version by sha256 (`supersedes` links a correction to what it replaces). Writes to `raw`. Runs layout analysis, splits pages into regions (`text`, `figure`, `scan`, `table`, `equation`, `code`) and routes each region by kind. Also ingests approved external exercises.
- **W2 vision** (offline and online, `workers/w2_vision`):
  - Ingest: OCR on scans and image tables, captions and alt text for figures.
  - Answer time: reads student photos of problem sets, charts and handwritten formulas into text and LaTeX.
- **W3 code** (offline and online, `workers/w3_code`):
  - Ingest: keeps R, SPSS and Python listings verbatim with a language tag.
  - Answer time: generates R, Python or Excel formula solutions, runs them in the sandbox and checks them against the draft answer.
- **W4 math** (offline and online, `workers/w4_math`):
  - Ingest: turns equations into normalized LaTeX.
  - Answer time: verifies calculations with SymPy and a catalogue of statistical operations (SciPy, statsmodels).
- **W5 clean** (offline and online, `workers/w5_clean`):
  - Ingest: normalizes text, removes boilerplate, deduplicates with MinHash, scrubs PII, scans for embedded instructions, writes the `cleaned` tier.
  - Answer time: cleans the question, uploaded text and fetched web pages, and scans them for injected instructions.
- **W6 embed** (offline and online, `workers/w6_embed`):
  - Ingest: chunks by structure (sections and pages, with equations and listings kept whole) and embeds, writing a candidate chunk set.
  - Answer time: embeds the query with the model pinned to the serving version.
- **W7 deepsearch** (online and offline, `workers/w7_deepsearch`):
  - Internal: hybrid search (pgvector dense plus Postgres full-text) on the pinned version, then rerank. Splits multi-hop questions.
  - External: when internal evidence is weak, searches allowlisted open textbook sites through SearXNG for matching exercises and answer keys.
  - Offline enrichment: scheduled external search by course topic, results queued as candidates.
- **W8 gen** (online, `workers/w8_gen`): builds the grounded prompt with the conversation history, streams the answer with chunk-level citations, and calls W4 and W3 as tools for calculations and code.

### Shared and offline parts

- **Quality gate** (offline, `libs/platform`, module `gate`): the only path into the `serving` tier (section 4.5).
- **Data platform** (shared, `libs/platform` and `libs/contracts`): object store, Postgres (serving index with pgvector, registry, ingest tiers, operational, evaluation and reporting tables), versioning, quality gate, lineage, retention and Parquet exports.
- **Model serving** (shared, configured in `infra/local`): LLM (base plus optional LoRA adapters), RAGAs judge, vision-language model, embedding and reranker models, guard classifiers.
- **Code sandbox** (shared, `workers/w3_code/sandbox`): runs untrusted generated code with no network and with CPU, memory and time limits. Only the api service, which runs W3, can reach it.
- **Eval runner** (offline, `ml/eval`): RAGAs on the golden set and sampled live traffic. Stores internal test runs (Appendix C.3).
- **Fine-tuning pipeline** (offline, optional and later, `ml/finetune`): dataset build, versioned split, SME approval gate, QLoRA training, evaluation, registry, promotion. It starts only when RAGAs shows that generation, not retrieval, limits answer quality.
- **Orchestration** (cross-cutting, `pipelines`): Dagster sensors, schedules and jobs. Each worker step runs in its own container from the app image.
- **Security and privacy** (cross-cutting, `infra/local` and `libs/common`): identity provider, keys, TLS, encryption at rest, pseudonymization keys, retention, audit log.
- **Observability** (cross-cutting, `libs/common` and `infra/local`): Prometheus metrics in the api service, a time per worker for every contract call, dashboards and alerts. OpenTelemetry traces and logs are an optional profile.

---

## 3. Running it locally

Every product, its version and licence, the compose profiles and the AWS mapping are in [../TECH_STACK.md](../TECH_STACK.md). In short: `data` is enough for data platform work, `data core cpu search sandbox dev` runs the full answer path on CPU, and the `gpu` profile is needed for the 10-user target. `traces` and `finetune` are optional.

---

## 4. The data platform

### 4.1 Storage layout

**Object store buckets**

- **`raw`:** source files exactly as received.
  Key `{sha256[0:2]}/{sha256}.{ext}`. Write-once. Kept for the life of the project.
- **`uploads`:** student attachments (photos, CSV, XLSX), encrypted.
  Key `{yyyy}/{mm}/{dd}/{request_id}/{attachment_id}`. Write-once. Short TTL because it is student data.
- **`external`:** snapshots of fetched external pages, for provenance.
  Key `{sha256[0:2]}/{sha256}.html`. Write-once. Kept until the candidate is rejected or superseded.
- **`exports`:** frozen datasets as Parquet files, such as fine-tuning dataset versions and the item scores of an evaluation run.
  Key `{name}/{sha256}.parquet`. Write-once. Kept for the life of the project.
- **`mlflow`:** model artifacts and adapters, when the fine-tuning phase starts.
  Append-only. Kept for the life of the project.

**Postgres database `chatbot`**

- **Schema `registry`:** `doc_versions`, `ingestion_runs`, `kb_versions`, `kb_aliases`, `gate_reports`. The source of truth for versions and aliases.
- **Schema `serving`:** `chunks` (content, vector and full-text columns, lineage columns) and `chunk_validity` (validity intervals). Read-only to the online plane.
- **Schema `ingest`:** `regions`, `extracted_regions`, `cleaned_pages` and `chunks`. The cleaned and chunked tiers, keyed by ingestion run.
- **Schema `ops`:** `interactions`, `conversations`, `citations`, `tool_calls`, `request_facts`, `guard_events`, `escalation_tickets`, `expert_rota`, `external_candidates`, `uploads`. Written by online services. These tables are both the hot data and the history.
- **Schema `eval`:** `ragas_scores`, `test_cases`, `test_runs`.
- **Schema `ft`:** `datasets`, `items`. Fine-tuning dataset versions.
- **Schema `reporting`:** daily views over `ops` and `registry` plus the `ragas_summary` table. The only schema Grafana can read, through the read-only `grafana_reader` role.

Separate databases on the same server hold Dagster and Keycloak state, and `chatbot_test` is wiped by the integration tests. Tables are defined in `libs/platform/src/chatbot_platform/sql.py` and created by Alembic migrations.

### 4.2 Tiers

- **raw:** files as received, in the `raw` bucket. Written by W1. Write-once.
- **cleaned:** page markdown, LaTeX, verbatim code, alt text and quality flags, in `ingest.regions`, `ingest.extracted_regions` and `ingest.cleaned_pages`. Written by W1 to W5. Kept, so a new embedding model rebuilds from here without new OCR.
- **chunked:** chunks with embeddings for a candidate knowledge base version, in `ingest.chunks`. Written by W6. Deleted by retention after 90 days, because publishing copies them into `serving.chunks`.
- **serving:** published knowledge base versions, in `serving.chunks`. Written by the quality gate only. Read-only to the online plane.

Every ingest row carries its `ingestion_run_id`. Writing the same record twice keeps one row, so a Dagster step that runs again after a failure is safe.

**One copy of operational data.** Online services write to `ops.*`, and reports, the lineage sweep and evaluation read the same tables. There is no copy job. Retention works in place: student free text is blanked after 365 days, operational rows are deleted after 730 days (section 8).

### 4.3 Versioning and reproducibility

- **Document version.** A new sha256 means a new `doc_version`. A correction carries `supersedes = <old doc_version>`.
- **Chunk identity is content-addressed:** `chunk_id = sha256(doc_version, page_span, text, chunker_version, embedding_model)`. Unchanged documents produce identical chunks, so correcting one document re-embeds only that document.
- **Knowledge base version.** An immutable manifest: the set of `doc_version`s, `chunker_version`, `embedding_model` and a gate report link. The aliases `serving` and `candidate` point at versions.
- **Storing chunks once.** Chunk content is stored once in `serving.chunks`. `serving.chunk_validity` holds its validity intervals `[valid_from_version, valid_to_version)`. The query filter is `valid_from_version <= vN < valid_to_version`. A chunk can have more than one interval: after a rollback, a later version can bring back a chunk that an intermediate version dropped.
- **Publishing.** Publishing version N compares it with the latest published version and with the parent of the candidate. It opens intervals for chunks that are new in N and closes those N dropped. Every step can be repeated safely, so a publish that stops halfway simply runs again. Rollback only moves the `serving` alias.
- **Reproducible retrieval.** Every answer logs `kb_version`, the retrieved `chunk_id`s with their scores, `model_version`, `prompt_version`, and any external sources used. Live serving uses HNSW, which is approximate. Audit replays use exact search restricted to the logged version, which is deterministic.
- **Reproducible datasets.** A dataset that must never change, such as a fine-tuning dataset version, is written once as a Parquet file in the `exports` bucket. Its key holds the file's sha256, and the dataset version is the hash of its item manifest.
- **Embedding-model change.** A new embedding model means a full new knowledge base version, built from the `cleaned` tier with no re-OCR, side by side with the current one (blue/green). W6 and W7 refuse to embed or query against a version whose `embedding_model` differs from their encoder.

### 4.4 Ingestion, re-ingestion and enrichment

1. A file lands in `raw` through the admin API or CLI, and a Dagster sensor fires.
2. W1 registers it. If the same `(course, source_id)` arrives with a new hash, it becomes a new `doc_version` that supersedes the old one.
3. W1 splits pages into regions. `REGION_HANDLERS` in `chatbot_contracts.knowledge_base` says which worker extracts each region kind. W2 to W6 process only that `doc_version`. W6 writes one `ChunkSet` per document version and run.
4. Candidate manifest = current `serving` manifest, minus the superseded version, plus the new one.
5. The quality gate runs. On a pass the version is published, the `serving` alias moves, and superseded chunks get `valid_to_version = vN+1`. Old versions stay reproducible.
6. **Lineage sweep.** A query over `ops.interactions` and `ops.citations` finds past answers that cited superseded chunks. They get a "source corrected since this answer" flag and a correction ticket goes to the SME queue.
7. **Retraction** (withdrawn with no replacement) follows the same path with removal only.
8. **External enrichment.** A weekly Dagster schedule asks W7 to search allowlisted sources for exercises with answer keys, by course topic. Answer-time external finds are queued the same way. Each find becomes an `external_candidates` row with its URL, snapshot, licence and the query that found it. An SME accepts or rejects it. Accepted candidates enter step 1 as `source_type = external_exercise` and go through the full gate.

### 4.5 The quality gate

**Automated checks.** Any failure blocks publication.
- Contract and schema validation on every record.
- Page coverage: every page of every `doc_version` has regions.
- OCR confidence at or above threshold. Anything below goes to SME review.
- Zero PII hits in chunks.
- Duplicate rate below threshold.
- Embedding sanity: dimension, norm, no NaNs, one embedding model per version.
- A licence is present for every `external_exercise` document.
- Retrieval regression on the golden set: recall@k and MRR no worse than the current `serving` version, within tolerance.
- RAGAs context precision and context recall on the golden set: no regression.

**Human sign-off.** SME approval is required for new source documents, corrections and external exercises. The SME reviews a chunk sample and a diff against the superseded version. Embedding refreshes need automated checks only.

**Output.** A gate report stored in `registry.gate_reports`, and a result: publish, or reject with reasons.

**Who owns which check.** The platform implements the structural checks (schema versions, chunk ids, page coverage, OCR confidence, PII, duplicate rate, embeddings, licences). The retrieval regression and RAGAs checks come from the eval lane (`ml/eval`). Until then they report *skipped*, which does not block.

### 4.6 Lineage

`citation → chunk_id → doc_version + page_start..page_end + region_ids → ingestion_run_id → raw object sha256`

For external exercises the chain continues to `external_candidate_id → url + snapshot sha256 + licence`. The ingestion run records the Dagster run ID, the app image digest and each model's version. Lineage is stored as columns at write time, never rebuilt from logs.

---

## 5. Query path, confidence and escalation

1. **Gateway.** Records `t0`. Checks auth, RBAC and rate limits, pseudonymizes the student, applies admission control and stores attachments in `uploads`. Takes the `conversation_id` from the request, or starts a new conversation.
2. **Guard, in parallel.** The gateway starts the injection and misuse guards and the orchestrator at the same time, and holds every event until the guard verdict arrives. An unsafe question cancels the answer, gets one error event, and is logged to `ops.guard_events`. The guard finishes long before generation, so it adds almost nothing to the latency.
3. **Orchestrator.** Pins `serving = vN`. Reads the last turns of the conversation from `ops.interactions` and, for a follow-up, asks the LLM to rewrite it as a standalone question.
4. **Input preparation.** W2 reads any attached image into text and LaTeX. W5 cleans the question and attachment text and scans it for injected instructions. W6 embeds the standalone question with the model pinned to vN.
5. **Internal retrieval.** W7 runs hybrid search on vN and reranks. It returns ranked chunks and a sufficiency score (top rerank score and margin).
6. **Generation.** W8 streams a cited answer, with the earlier turns in the prompt, and records `t_first_token`. It calls W4 for calculations and statistics and W3 for R, Python or Excel work.
7. **Citation validator.** Every cited `chunk_id` must be in the retrieved set. Otherwise the citation is stripped and confidence drops.
8. **Confidence** is a score from 0 to 1 built from four signals: top rerank score and margin, NLI groundedness per sentence, citation coverage, and the guard verdict. It starts with hand-set weights, then moves to logistic regression calibrated on SME-labelled answers. The score maps to a level:
   - **L1**, score 0.75 or more: answer.
   - **L2**, score from 0.50 to 0.75: answer with a caveat and suggested sources.
   - **L3**, score below 0.50: escalate (steps 9 and 10).

   The thresholds are placeholders to tune on data. If the sufficiency score from step 5 is below a floor, the orchestrator skips the first draft and goes straight to step 9.
9. **L3, first: external sources.**
   - The student receives `status.external_search` ("this question is complex, checking external sources").
   - A ticket is logged with the question (pseudonymized), the retrieved context and the confidence.
   - W7 searches allowlisted external sources with a PII-stripped query.
   - W5 cleans the fetched pages and scans them for injected instructions.
   - W8 regenerates with the external context labelled "unvetted external source", and the answer is scored again. At L2 or above it is sent.
   - The finds are queued as enrichment candidates.
10. **L3, second: human expert.** If the answer is still L3, or no external source is found, the escalation service notifies the on-duty expert. The student receives `status.expert_pending` with the expected wait. The expert answers through the API and the answer reaches the student later as `answer.expert`. It can be proposed as a golden-set item or a knowledge base correction.
11. The orchestrator logs the interaction with its `conversation_id`, and the gateway records `t_last_byte` and writes `ops.request_facts`.

Steps 3 to 10 run inside the api process. Every call between components goes through `ContractClient`, as a function call, and is timed per worker.

**Runtime levels and test levels.** L1 to L3 above are runtime confidence levels. The internal testing Levels 1 to 3 in Appendix C are categories of test questions. Level 3 testing checks that low-confidence questions trigger steps 9 and 10.

**Metric definitions**
- **Latency:** `t_first_token − t0`, plus the time of every worker call.
- **End-to-end response time:** `t_last_byte − t0`.
- **Throughput:** completed requests per minute and output tokens per second.
- **Escalation rate:** L3 requests divided by all requests.
- **External response time:** from escalation start to external answer sent, reported as p50 and p95.
- **Expert response time:** from ticket created to expert answer submitted, reported as p50 and p95.

---

## 6. Evaluation and observability as data products

Each entry reads: **table** (one row per ...): key columns.

- **`ops.request_facts`** (one row per request, blocked ones included): request_id, level, latency_ms, e2e_ms, tokens_in, tokens_out, guard_verdict, attachment_count, created_at.
- **`ops.interactions`** (one row per answered request): request_id, conversation_id, pseudo_user, question (encrypted), answer, kb_version, model_version, prompt_version, confidence, level, used_external, escalated, source_corrected, created_at.
- **`ops.guard_events`** (one row per detection): request_id, detector, stage (`gateway`, `w5_online`, `w5_ingest`), category, score, action, created_at.
- **`ops.tool_calls`** (one row per W3 or W4 call): request_id, tool, operation, language, duration_ms, verdict, error.
- **`ops.escalation_tickets`** (one row per ticket): ticket_id, request_id, question (encrypted), context_ids, confidence, external_results, external_response_ms, expert, created_at, answered_at.
- **`eval.ragas_scores`** (one row per item, metric and run): run_id, kb_version, model_version, prompt_version, dataset (`golden` or `live_sample`), item_id, metric, score, judge_model, created_at.
- **`eval.test_cases` and `eval.test_runs`** (one row per test question and per run): level (1 to 3), question, source, response, RAGAs scores, escalated, remediation. This is the Appendix C.3 test documentation.
- **Resource use** (Prometheus, not a table): CPU and memory per container from cAdvisor, GPU from the DCGM exporter, and the time of every call per worker from `chatbot_worker_call_seconds`. Prometheus keeps 90 days, enough for a milestone review.

**Data flow.** The api service exposes Prometheus metrics on `/metrics`, with names defined once in `chatbot_common.metrics`. Prometheus scrapes them. Tables above are written directly by the components that own them. Traces and logs go through the OpenTelemetry Collector to Tempo and Loki when the optional `traces` profile runs.

**Dashboards.** Four Grafana dashboards, stored as JSON in `infra/local/grafana/dashboards`: Performance (B.1), Safety and misuse (B.2), Resources (B.3), Quality and escalation (A.6, C.2). They read Prometheus and the Postgres `reporting` schema. `scripts/check_dashboards.py` keeps them in line with the metric catalogue and the schema. See [MONITORING.md](../MONITORING.md).

**RAGAs schedule.**
- Golden set, all four metrics: at every candidate knowledge base version (as part of the gate), at every model promotion, and nightly.
- Sampled live traffic, reference-free metrics: nightly and off-peak, pseudonymized rows only.
- The judge comes from another model family than the generator, so it does not favour its own answers. It is calibrated against an SME-labelled set, and its version is stored on every score.

---

## 7. Fine-tuning pipeline

This phase is optional and comes later. It starts only when RAGAs shows that generation, not retrieval, limits answer quality. MLflow runs in the `finetune` compose profile.

1. **Sources.** SME-written Q&A, plus synthetic Q&A generated from knowledge base version vN and reviewed by SMEs. Student interactions only if conflict 4 allows it.
2. **Build.** Deduplicate and scan for PII. Check for leakage against the golden and test sets. Split deterministically by `hash(item_id)` into 80/10/10, stratified by course and topic.
3. **Version.** Freeze the dataset as a write-once Parquet file in the `exports` bucket, plus `ft.items` rows and an `ft.datasets` row with the export URI. The hash of the item manifest is the `dataset_version`.
4. **SME approval gate.** SMEs approve or reject through the API, with a comment. Training refuses any unapproved `dataset_version`.
5. **Train.** QLoRA on the serving base model. Seed, config and container digest are recorded.
6. **Evaluate.** On the test split plus the RAGAs golden set, against the current production model.
7. **Register.** In MLflow, with lineage to `dataset_version` and `kb_version`.
8. **Promote.** Manually. The LLM server hot-loads the adapter. Rollback switches the adapter version.

---

## 8. Security and privacy

- **In transit:** TLS at Traefik locally, service-to-service TLS in the cloud phase. Traefik exposes only the public routes of the api service.
- **At rest:** object store encryption. Postgres on an encrypted volume, with column encryption for free-text student questions and answers (envelope keys from the key service).
- **Keys:** every key goes through the `KeyService` port (`chatbot_common.keys`). Locally it reads a key file mounted read-only into the api container. On AWS it uses KMS and Secrets Manager. Keys come in epochs.
- **RBAC roles:** `student`, `sme`, `expert`, `data_engineer`, `ml_engineer`, `ops`, `auditor`. Enforced in Postgres (roles and row-level security), in bucket policies, and behind Keycloak for Dagster, Grafana and MLflow.
- **Pseudonymization:** `pseudo_user = HMAC-SHA256(key_epoch, student_id)`, with the key from the key service. Free text is PII-scrubbed with Presidio before any fine-tuning or evaluation use.
- **Uploads:** student attachments are student data. They are encrypted, have a short TTL, are never sent outside the system and are never used for training.
- **External search:** allowlisted domains only, `robots.txt` respected, rate limits honoured, PII-stripped queries, licence recorded, content cleaned and scanned before W8 sees it, answers labelled "unvetted external source".
- **Code sandbox:** a separate container on an internal network with no internet access. Non-root, read-only root filesystem, temporary work directory, CPU, memory and wall-clock limits, one job per process.
- **Retention:** each table has a TTL enforced by a daily Dagster sweep, in place. Uploads go after 30 days. Student free text in `ops.interactions` and `ops.escalation_tickets` is blanked after 365 days. Operational rows go after 730 days. Staged chunks go after 90 days. Database backups must not outlive the operational TTL. Pseudonym key epochs are destroyed at expiry (crypto-shredding).
- **Fail closed:** if the key service is unavailable, the gateway rejects requests rather than logging raw IDs.

---

## 9. Data contracts

Contracts live in `libs/contracts` (Pydantic v2). JSON Schema is exported from it and CI checks backward compatibility. Every record carries `schema_version`, the producer worker plus its image digest, and `ingestion_run_id` (offline) or `request_id` (online).

Each entry reads: **contract** (producer → consumer): key fields. A pair like `A / B` means request fields / response fields.

- **`DocumentVersion`** (upload → platform, W1 adds page_count): doc_id, doc_version, sha256, source_type (`textbook`, `lecture_note`, `past_exam`, `answer_key`, `external_exercise`), course_code, source_id, raw_uri, licence, source_url, page_count, supersedes.
- **`Region`** (W1 → W2, W3, W4, W5): region_id, doc_version, page_no, bbox, kind, raw_text, image_uri.
- **`ExtractedRegion`** (W2, W3, W4 → W5): region_id, kind, content (markdown, LaTeX or code), extractor name and version, confidence.
- **`CleanPage`** (W5 → W6, one per page): doc_version, page_no, markdown, region_ids, flags (min_ocr_conf, pii_hits, pii_remaining, dup_of, injection_hits).
- **`ChunkSet`** (W6 → quality gate, one per document version and run): doc_version, embedding_model, chunker_version, and chunks with chunk_id, doc_version, page_start, page_end, section_path, text, kinds, token_count, region_ids, embedding.
- **`KnowledgeBaseManifest`** (quality gate → serving): version_id, parent_version, doc_versions, embedding_model, chunker_version, status, gate_report_id.
- **`AskRequest`** (gateway → orchestrator): request_id, pseudo_user, conversation_id, question, attachments.
- **`Attachment`** (gateway → orchestrator): attachment_id, request_id, media_type, uri, sha256, size_bytes.
- **`VisionRequest` / `VisionResult`** (orchestrator ↔ W2): attachment / text, latex, detected_kind, confidence.
- **`CleanRequest` / `CleanResult`** (orchestrator and W7 ↔ W5): text, origin (`question`, `upload`, `external`) / text, pii_hits, injection_hits, dropped.
- **`EmbedRequest` / `EmbedResult`** (orchestrator ↔ W6): texts, kb_version / vectors, embedding_model.
- **`RetrievalRequest` / `RetrievalResult`** (orchestrator ↔ W7): request_id, question, query_vector, kb_version, k, filters / chunks with chunk_id, dense, lexical, rerank, doc_version, page, plus sufficiency and timings.
- **`ExternalSearchRequest` / `ExternalSearchResult`** (orchestrator ↔ W7): request_id, query (PII-stripped), topics, max_results / items with url, title, snippet, licence, snapshot_uri, score, plus timings.
- **`ExternalCandidate`** (W7 → platform): candidate_id, url, snapshot_sha256, licence, course_code, topic, found_by (`answer_time` or `enrichment`), status.
- **`GenerationRequest` / `GenerationResult`** (orchestrator ↔ W8): request_id, question, contexts, external_contexts, history (earlier `Turn`s, question and answer), model_version, prompt_version / answer, citations (chunk_id or url, doc_version, page), tool_calls, tokens, timings.
- **`CalcCheck` / `CalcResult`** (W8 → W4): operation, expression, variables, units / value, valid, explanation.
- **`CodeTask` / `CodeResult`** (W8 → W3): language (`r`, `python`, `excel`), task, data_uri, expected / code, stdout, values, verdict, duration_ms.
- **`EscalationTicket`** (orchestrator → escalation): ticket_id, request_id, pseudo_user, question, context_ids, confidence, external_results, status, expert, timestamps.
- **`TicketQuery`** (gateway → escalation): request_id. Returns the `EscalationTicket` of that request, for late expert answers.
- **`StreamEvent`** (orchestrator → gateway → student, server-sent events): type (`answer.delta`, `answer.final`, `status.external_search`, `status.expert_pending`, `answer.expert`, `error`), text, citations, level, conversation_id.

Every online endpoint, with its request and response record, is defined once in `chatbot_contracts.routes`. Each component exposes the functions that answer its endpoints as `HANDLERS`. The api service calls them in process, and `add_contract_routes` serves the same functions over HTTP when a component runs alone. `chatbot_contracts.samples` has a valid sample of every record for tests.

---

## 10. Failure modes

Each entry reads: **failure**, then what happens, how we detect it, and how we handle it.

- **GPU out of memory or LLM server crash**
  Effect: no answers. Detected by: health check, error-rate alert. Handled by: restart policy. The gateway returns 503 with retry-after. CPU fallback only when flagged as degraded.
- **More than 10 concurrent users**
  Effect: latency breach. Detected by: latency p95 alert. Handled by: continuous batching, admission queue, streaming.
- **A CPU-heavy step blocks the api process**
  Effect: every request in flight slows down. Detected by: time per worker, latency p95. Handled by: CPU-bound work runs in worker threads. If one worker still dominates, move it to its own container with `CHATBOT_<SERVICE>_URL`.
- **The api process crashes**
  Effect: the whole answer path is down for a moment. Detected by: health check, targets up. Handled by: restart policy. Tickets and logs are in Postgres, so nothing is lost. A second replica behind Traefik removes the gap if needed.
- **Retrieval finds nothing relevant**
  Effect: risk of hallucination. Detected by: low sufficiency, low confidence. Handled by: external search, then the expert. Never answer without citations.
- **W8 cites a chunk it did not retrieve**
  Effect: fabricated citation. Detected by: citation validator. Handled by: strip or regenerate, lower confidence.
- **A follow-up is rewritten wrongly**
  Effect: retrieval answers another question. Detected by: low confidence, RAGAs on sampled conversations. Handled by: the rewrite prompt is versioned and tuned on follow-up items of the golden set. A low confidence answer still takes the L2 or L3 path.
- **A bad document passes (OCR garbage)**
  Effect: wrong answers. Detected by: gate checks, SME sample, RAGAs drop. Handled by: move `serving` back to the previous version.
- **A correction arrives after answers cited the old page**
  Effect: stale citation. Detected by: lineage sweep. Handled by: flag affected answers, open an SME ticket.
- **Query encoder differs from the index's embedding model**
  Effect: nonsense retrieval. Detected by: version check in W6 and W7. Handled by: refuse and alert.
- **A pipeline worker fails mid-run**
  Effect: partial candidate. Detected by: Dagster run status. Handled by: retries, which rewrite the same ingest rows. A candidate without a complete manifest can never publish.
- **Instructions hidden in sources or web pages**
  Effect: the model follows injected text. Detected by: W5 injection scan, guard on retrieved chunks. Handled by: quarantine the region or page. Sources stay in a separate data role in the prompt.
- **External search down or rate-limited**
  Effect: escalation delay. Detected by: timeout. Handled by: skip to the expert.
- **Generated code misbehaves (loop, fork, large output)**
  Effect: resource exhaustion. Detected by: sandbox limits. Handled by: kill on limit, return verdict `error`, W8 answers without the code result.
- **Unreadable student photo**
  Effect: wrong question text. Detected by: W2 confidence. Handled by: ask the student to retype or retake the photo.
- **No expert on duty**
  Effect: the ticket waits. Detected by: rota coverage check, response-time timer. Handled by: fall back to the course coordinator and tell the student the expected wait.
- **RAGAs judge drift**
  Effect: misleading scores. Detected by: calibration set. Handled by: recalibrate. The judge version is stored on every score.
- **Key service unavailable (key file missing, KMS down)**
  Effect: cannot pseudonymize. Detected by: health check. Handled by: fail closed.
- **Retention sweep fails**
  Effect: data kept too long. Detected by: sweep job alert, audit. Handled by: re-run. Every rule is a delete or update in place, so a re-run is safe.

---

## 11. Constraint conflicts (still open)

1. **Free-tier budget vs. self-hosted inference for 10 concurrent users.** No GPU instance is free-tier eligible. Locally, this becomes a hardware requirement for load tests only.
2. **External sources vs. the quality gate.** Resolved. External content is used at answer time only with an "unvetted" label, and enters the knowledge base only through the gate with SME sign-off.
3. **RAGAs "on an ongoing basis" vs. a self-hosted judge and latency.** Context recall needs reference answers, so it runs on the golden set. Live traffic gets reference-free metrics, sampled and off-peak.
4. **Retention limits vs. a reproducible fine-tuning dataset.** Decision needed. Options:
   - (a) SME-written and synthetic data only
   - (b) reproducible only within the retention window
   - (c) irreversible anonymization before a row enters a dataset
5. **Per-worker resources in one process.** Online workers share the api container, so CPU and memory are measured per container and per model server, and each worker gets its time per call. GPU memory per process is exact, GPU utilization per process is only sampled.
6. **Vision and code on the answer path vs. latency on CPU.** A vision-language model and sandboxed R add seconds per request on CPU. The latency thresholds (Appendix D, still TBD) must be measured with and without attachments.

## 12. Assumptions to confirm

- Latency, response time, throughput and RAGAs thresholds (Appendix D, still TBD).
- "Photographed problem sets" means student uploads at answer time.
- The student frontend can upload attachments, show SSE status events, fetch late expert answers, and send back the `conversation_id` it receives for follow-up questions.
- The external domain allowlist needs Institution approval before M6.
- SME approvals and expert answers are backend APIs plus email, with no new UI.

---

## 13. Repository map

```
AI-chatbot/
  README.md, pyproject.toml, uv.lock, compose.yaml, .env.example
  docs/
    TECH_STACK.md, MONITORING.md, CHANGELOG.md
    architecture/              this file and diagrams/
  libs/
    contracts/                 chatbot_contracts: records, routes, samples, JSON schemas
    platform/                  chatbot_platform: storage, registry, index, ingest tiers, versioning, gate, lineage, retention, exports
    common/                    chatbot_common: app factory, contract client and local handlers, keys, test fakes, model clients
  services/
    api/                       chatbot_api: the api service, every online component in one process
    gateway/                   chatbot_gateway
    orchestrator/              chatbot_orchestrator
    escalation/                chatbot_escalation
  workers/
    w1_ingest/   w2_vision/   w3_code/ (with sandbox/)   w4_math/
    w5_clean/    w6_embed/    w7_deepsearch/             w8_gen/
  pipelines/                   chatbot_pipelines: Dagster code location
  ml/
    eval/                      chatbot_eval: golden set, RAGAs, gate checks, test runs
    finetune/                  chatbot_finetune: dataset, approval, QLoRA, registry (optional phase)
  infra/
    docker/                    one Dockerfile for every Python package
    local/                     config for Postgres, SeaweedFS, Keycloak, Traefik, SearXNG, Dagster, OTel, Grafana, and the local key file
    aws/terraform/             phase 2
  scripts/                     comment rule, lane boundaries, dashboard check, test runner
  tests/                       tests across packages and the Locust load test
```

Services, workers, pipelines and ml packages depend only on the three libraries. They talk to each other through contracts, never through imports. The api package is the only one allowed to import services and workers, to compose them into one process, and nothing may import it. `scripts/check_boundaries.py` enforces this in CI.
