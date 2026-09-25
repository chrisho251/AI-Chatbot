# AI-chatbot: backend architecture

**Version:** 1.0 (local first)
**Date:** 2026-09-25
**Scope:** backend only. The student frontend already exists and lives outside this repo.
**Read this when:** you need to know how the system works: which component does what, how data moves, how versions, security and failures are handled.
**Not in this file:** product names, versions, licences and machine setup. Those are in [../TECH_STACK.md](../TECH_STACK.md).

**Related documents**
- [../TECH_STACK.md](../TECH_STACK.md): every service, tool, model and database, with portability notes and compose profiles.
- [../MONITORING.md](../MONITORING.md): metrics, dashboards and how to maintain them.

**Diagrams** (drawn with Archify; each HTML is interactive, with a PNG and its JSON source next to it in [diagrams/](diagrams/))
- [01 System architecture](diagrams/01-system-architecture.html): the whole system on one page, grouped by plane, with code paths.
- [02 Worker map](diagrams/02-worker-map.html): the eight workers in their offline and online roles, and the contracts between them.
- [03 RAG pipeline](diagrams/03-rag-pipeline.html): one student question to a cited answer, an external-source answer, or an expert escalation.
- [04 Ingestion](diagrams/04-ingestion.html): how an uploaded PDF or an external exercise becomes a published corpus version.

**Deployment stance.** Phase 1 runs everything as containers on any team machine with Docker Compose. Phase 2 moves to AWS. Every infrastructure dependency sits behind a port (an interface), so the move swaps adapters and infrastructure code, not application logic.

---

## 1. Design principles

1. **Two planes, one platform.** The *online plane* answers students and is bound by latency. The *offline plane* builds the corpus and is bound by throughput. They share the data platform and model serving.
2. **One worker, one image, two entrypoints.** Each of the eight workers is its own image. A worker used in both planes exposes `serve` (online HTTP API) and `job` (offline Dagster step) from the same image, so both roles share code, metric labels and a contract boundary.
3. **Internal first, external second.** Answers come from the vetted corpus. The external web is a fallback, always labelled "unvetted external source", and never enters the corpus without the quality gate and SME sign-off.
4. **The corpus is immutable and versioned.** A corrected document becomes a new document version, which becomes a new corpus version. Serving points at a version through an alias, so rollback means moving the alias.
5. **Contracts, not shared tables.** Workers exchange typed, versioned records. No worker reads another worker's storage.
6. **Ports and adapters for all infrastructure.** Object store, catalog, query engine, index, lineage, identity, secrets, mail, web search, code runner and metrics are interfaces with a local adapter and an AWS adapter.
7. **Operational data is platform data.** RAGAs scores, latency, throughput, guard events, escalations, tool calls and resource use land as tables with history.
8. **Privacy by construction.** Student identity is pseudonymized at the gateway. Nothing downstream sees a real student ID. Outbound external queries are PII-stripped.
9. **Portable by default.** CPU and multi-architecture images by default, GPU as an optional profile, every endpoint in configuration.

---

## 2. Components and responsibilities

Worker names follow Appendix A.4: W1 Worker-ingest, W2 Worker-vision, W3 Worker-code, W4 Worker-math, W5 Worker-clean, W6 Worker-embed, W7 Worker-deepsearch, W8 Worker-gen.

Each entry reads: **component** (plane, code folder): what it does.

### Online services

- **API gateway** (online, `services/gateway`): validates OIDC tokens, enforces RBAC, rate limits and admission control. Pseudonymizes the student. Runs the prompt-injection and misuse guards. Accepts attachments into `uploads`. Streams answers and status events over SSE. Records `t0`, `t_first_token` and `t_last_byte`.
- **Query orchestrator** (online, `services/orchestrator`): pins the `serving` corpus version per request. Runs input preparation (W2, W5, W6), retrieval (W7), generation (W8), citation validation and confidence scoring. Routes L1, L2 or L3 and logs the interaction.
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
  - External: when internal evidence is weak, searches allowlisted web sources through SearXNG and free APIs for matching exercises and answer keys.
  - Offline enrichment: scheduled external search by course topic, results queued as candidates.
- **W8 gen** (online, `workers/w8_gen`): builds the grounded prompt, streams the answer with chunk-level citations, and calls W4 and W3 as tools for calculations and code.

### Shared and offline parts

- **Quality gate** (offline, `libs/platform`, module `gate`): the only path into the `serving` tier (section 4.5).
- **Data platform** (shared, `libs/platform` and `libs/contracts`): object store, Iceberg tables, Postgres and pgvector serving index, registry and lineage, versioning, quality gate, retention.
- **Model serving** (shared, configured in `infra/local`): LLM (base plus LoRA adapters), RAGAs judge, vision-language model, embedding and reranker models, guard classifiers.
- **Code sandbox** (shared, `workers/w3_code/sandbox`): runs untrusted generated code with no network and with CPU, memory and time limits. Only W3 can reach it.
- **Eval runner** (offline, `ml/eval`): RAGAs on the golden set and sampled live traffic. Stores internal test runs (Appendix C.3).
- **Fine-tuning pipeline** (offline, `ml/finetune`): dataset build, versioned split, SME approval gate, QLoRA training, evaluation, registry, promotion.
- **Orchestration** (cross-cutting, `pipelines`): Dagster sensors, schedules and jobs. Each worker step runs in its own image.
- **Security and privacy** (cross-cutting, `infra/local` and `libs/common`): identity provider, keys, TLS, encryption at rest, pseudonymization keys, retention, audit log.
- **Observability** (cross-cutting, `libs/common` and `infra/local`): OpenTelemetry in every service, real-time stores, dashboards and alerts, hourly snapshots into the platform.

---

## 3. Running it locally

Every product, its version and licence, the compose profiles and the AWS mapping are in [../TECH_STACK.md](../TECH_STACK.md). In short: `data` is enough for data platform work, `data core cpu search sandbox dev` runs the full answer path on CPU, and the `gpu` profile is needed for the 10-user target.

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
- **`warehouse`:** data and metadata files of every Iceberg table.
  Managed by Iceberg. TTL per table.
- **`mlflow`:** model artifacts and adapters.
  Append-only. Kept for the life of the project.

**Postgres database `chatbot`**

- **Schema `registry`:** `doc_versions`, `ingestion_runs`, `corpus_versions`, `corpus_aliases`, `gate_reports`. The source of truth for versions and aliases.
- **Schema `serving`:** `chunks` (content, vector and full-text columns, lineage columns) and `chunk_validity` (validity intervals). Read-only to the online plane.
- **Schema `ops`:** `interactions`, `citations`, `tool_calls`, `escalation_tickets`, `expert_rota`, `external_candidates`, `uploads`. Hot operational rows written by online services.
- **Schema `reporting`:** daily views over `ops` and `registry` plus the `ragas_summary` table. The only schema Grafana can read, through the read-only `grafana_reader` role.
- **Iceberg SQL catalog:** PyIceberg creates its two catalog tables in the `public` schema.

Separate databases on the same server hold Dagster and Keycloak state, and `chatbot_test` is wiped by the integration tests. Tables are defined in `libs/platform/src/chatbot_platform/sql.py` and created by Alembic migrations.

**Iceberg namespaces**

- **`corpus`:** `regions`, `extracted_regions`, `cleaned_pages`, `chunks`
- **`external`:** `candidates`, `fetches`
- **`interactions`:** `requests`, `citations`, `tool_calls`
- **`eval`:** `ragas_scores`, `test_cases`, `test_runs`
- **`obs`:** `request_facts`, `worker_resources`, `guard_events`
- **`escalation`:** `tickets`
- **`ft`:** `datasets`, `items`
- **`gate`:** `reports`

### 4.2 Tiers

- **raw:** files as received, in the `raw` bucket. Written by W1. Write-once.
- **cleaned:** page markdown, LaTeX, verbatim code, alt text and quality flags, in `corpus.regions`, `corpus.extracted_regions` and `corpus.cleaned_pages`. Written by W1 to W5. Append-only snapshots.
- **chunked:** chunks with embeddings for a candidate corpus version, in `corpus.chunks`. Written by W6. Append-only snapshots.
- **serving:** published corpus versions, in `serving.chunks`. Written by the quality gate only. Read-only to the online plane.

**Hot and history.** Online services write to `ops.*` in Postgres because it is fast and transactional. An hourly Dagster job copies new rows into the Iceberg history tables (`interactions.*`, `escalation.tickets`, `external.candidates`). Reports, the lineage sweep and evaluation read the Iceberg side. Retention deletes from both.

### 4.3 Versioning and reproducibility

- **Document version.** A new sha256 means a new `doc_version`. A correction carries `supersedes = <old doc_version>`.
- **Chunk identity is content-addressed:** `chunk_id = sha256(doc_version, page_span, text, chunker_version, embedding_model)`. Unchanged documents produce identical chunks, so correcting one document re-embeds only that document.
- **Corpus version.** An immutable manifest: the set of `doc_version`s, `chunker_version`, `embedding_model` and a gate report link. The aliases `serving` and `candidate` point at versions.
- **Storing chunks once.** Chunk content is stored once in `serving.chunks`. `serving.chunk_validity` holds its validity intervals `[valid_from_version, valid_to_version)`. The query filter is `valid_from_version <= vN < valid_to_version`. A chunk can have more than one interval: after a rollback, a later version can bring back a chunk that an intermediate version dropped.
- **Publishing.** Publishing version N compares it with the latest published version and with the parent of the candidate. It opens intervals for chunks that are new in N and closes those N dropped. Every step can be repeated safely, so a publish that stops halfway simply runs again. Rollback only moves the `serving` alias.
- **Reproducible retrieval.** Every answer logs `corpus_version`, the retrieved `chunk_id`s with their scores, `model_version`, `prompt_version`, and any external sources used. Live serving uses HNSW, which is approximate. Audit replays use exact search restricted to the logged version, which is deterministic.
- **Embedding-model change.** A new embedding model means a full new corpus version, built from the `cleaned` tier with no re-OCR, side by side with the current one (blue/green). W6 and W7 refuse to embed or query against a version whose `embedding_model` differs from their encoder.

### 4.4 Ingestion, re-ingestion and enrichment

1. A file lands in `raw` through the admin API or CLI, and a Dagster sensor fires.
2. W1 registers it. If the same `(course, source_id)` arrives with a new hash, it becomes a new `doc_version` that supersedes the old one.
3. W1 splits pages into regions. `REGION_HANDLERS` in `chatbot_contracts.corpus` says which worker extracts each region kind. W2 to W6 process only that `doc_version`. W6 writes one `ChunkSet` per document version and run.
4. Candidate manifest = current `serving` manifest, minus the superseded version, plus the new one.
5. The quality gate runs. On a pass the version is published, the `serving` alias moves, and superseded chunks get `valid_to_version = vN+1`. Old versions stay reproducible.
6. **Lineage sweep.** A query over `interactions` finds past answers that cited superseded chunks. They get a "source corrected since this answer" flag and a correction ticket goes to the SME queue.
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

**Output.** A gate report stored in `registry.gate_reports` and `gate.reports`, and a result: publish, or reject with reasons.

**Who owns which check.** The platform implements the structural checks (schema versions, chunk ids, page coverage, OCR confidence, PII, duplicate rate, embeddings, licences). The retrieval regression and RAGAs checks come from the eval lane (`ml/eval`). Until then they report *skipped*, which does not block.

### 4.6 Lineage

`citation → chunk_id → doc_version + page_start..page_end + region_ids → ingestion_run_id → raw object sha256`

For external exercises the chain continues to `external_candidate_id → url + snapshot sha256 + licence`. The ingestion run records the Dagster run ID, each worker's image digest and each model's version. Lineage is stored as columns at write time, never rebuilt from logs.

---

## 5. Query path, confidence and escalation

1. **Gateway.** Records `t0`. Checks auth, RBAC and rate limits, pseudonymizes the student, runs the injection and misuse guards, applies admission control and stores attachments in `uploads`. Unsafe requests are blocked and logged to `obs.guard_events`.
2. **Orchestrator.** Pins `serving = vN`.
3. **Input preparation.** W2 reads any attached image into text and LaTeX. W5 cleans the question and attachment text and scans it for injected instructions. W6 embeds the query with the model pinned to vN.
4. **Internal retrieval.** W7 runs hybrid search on vN and reranks. It returns ranked chunks and a sufficiency score (top rerank score and margin).
5. **Generation.** W8 streams a cited answer and records `t_first_token`. It calls W4 for calculations and statistics and W3 for R, Python or Excel work.
6. **Citation validator.** Every cited `chunk_id` must be in the retrieved set. Otherwise the citation is stripped and confidence drops.
7. **Confidence** is a score from 0 to 1 built from four signals: top rerank score and margin, NLI groundedness per sentence, citation coverage, and the guard verdict. It starts with hand-set weights, then moves to logistic regression calibrated on SME-labelled answers. The score maps to a level:
   - **L1**, score 0.75 or more: answer.
   - **L2**, score from 0.50 to 0.75: answer with a caveat and suggested sources.
   - **L3**, score below 0.50: escalate (steps 8 and 9).

   The thresholds are placeholders to tune on data. If the sufficiency score from step 4 is below a floor, the orchestrator skips the first draft and goes straight to step 8.
8. **L3, first: external sources.**
   - The student receives `status.external_search` ("this question is complex, checking external sources").
   - A ticket is logged with the question (pseudonymized), the retrieved context and the confidence.
   - W7 searches allowlisted external sources with a PII-stripped query.
   - W5 cleans the fetched pages and scans them for injected instructions.
   - W8 regenerates with the external context labelled "unvetted external source", and the answer is scored again. At L2 or above it is sent.
   - The finds are queued as enrichment candidates.
9. **L3, second: human expert.** If the answer is still L3, or no external source is found, the escalation service notifies the on-duty expert. The student receives `status.expert_pending` with the expected wait. The expert answers through the API and the answer reaches the student later as `answer.expert`. It can be proposed as a golden-set item or a corpus correction.
10. The gateway records `t_last_byte`.

**Runtime levels and test levels.** L1 to L3 above are runtime confidence levels. The internal testing Levels 1 to 3 in Appendix C are categories of test questions. Level 3 testing checks that low-confidence questions trigger steps 8 and 9.

**Metric definitions**
- **Latency:** `t_first_token − t0`, plus a span per worker.
- **End-to-end response time:** `t_last_byte − t0`.
- **Throughput:** completed requests per minute and output tokens per second.
- **Escalation rate:** L3 requests divided by all requests.
- **External response time:** from escalation start to external answer sent, reported as p50 and p95.
- **Expert response time:** from ticket created to expert answer submitted, reported as p50 and p95.

---

## 6. Evaluation and observability as data products

Each entry reads: **table** (one row per ...): key columns.

- **`obs.request_facts`** (one row per request): request_id, ts, pseudo_user, corpus_version, model_version, prompt_version, latency_ms, e2e_ms, tokens_in, tokens_out, confidence, level, guard_verdict, used_external, escalated, attachment_count.
- **`obs.worker_resources`** (one row per worker every 15 s): ts, worker, role (`serve` or `job`), container, cpu_pct, mem_bytes, gpu_mem_bytes, gpu_util_pct.
- **`obs.guard_events`** (one row per detection): ts, request_id, detector, stage (`gateway`, `w5_online`, `w5_ingest`), category, score, action.
- **`interactions.tool_calls`** (one row per W3 or W4 call): request_id, tool, operation, language, duration_ms, verdict, error.
- **`eval.ragas_scores`** (one row per item, metric and run): run_id, ts, corpus_version, model_version, prompt_version, dataset (`golden` or `live_sample`), item_id, metric, score, judge_model.
- **`eval.test_cases` and `eval.test_runs`** (one row per test question and per run): level (1 to 3), question, source, response, RAGAs scores, escalated, remediation. This is the Appendix C.3 test documentation.
- **`escalation.tickets`** (one row per ticket): ticket_id, request_id, question, context_ids, confidence, external_result, external_response_ms, expert, created_at, answered_at.

**Data flow.** Every service exposes Prometheus metrics on `/metrics`, with names defined once in `chatbot_common.metrics`. Prometheus scrapes them (real time, short retention). Traces and logs go through the OpenTelemetry Collector to Tempo and Loki. An hourly Dagster job snapshots operational data into Iceberg (history, long retention).

**Dashboards.** Four Grafana dashboards, stored as JSON in `infra/local/grafana/dashboards`: Performance (B.1), Safety and misuse (B.2), Resources (B.3), Quality and escalation (A.6, C.2). They read Prometheus and the Postgres `reporting` schema. `scripts/check_dashboards.py` keeps them in line with the metric catalogue and the schema. See [MONITORING.md](../MONITORING.md).

**RAGAs schedule.**
- Golden set, all four metrics: at every candidate corpus version (as part of the gate), at every model promotion, and nightly.
- Sampled live traffic, reference-free metrics: nightly and off-peak, pseudonymized rows only.
- The judge is calibrated against an SME-labelled set, and its version is stored on every score.

---

## 7. Fine-tuning pipeline

1. **Sources.** SME-written Q&A, plus synthetic Q&A generated from corpus version vN and reviewed by SMEs. Student interactions only if conflict 4 allows it.
2. **Build.** Deduplicate and scan for PII. Check for leakage against the golden and test sets. Split deterministically by `hash(item_id)` into 80/10/10, stratified by course and topic.
3. **Version.** Freeze the dataset as an Iceberg snapshot plus a manifest of item hashes. That manifest is the `dataset_version`.
4. **SME approval gate.** SMEs approve or reject through the API, with a comment. Training refuses any unapproved `dataset_version`.
5. **Train.** QLoRA on the serving base model. Seed, config and container digest are recorded.
6. **Evaluate.** On the test split plus the RAGAs golden set, against the current production model.
7. **Register.** In MLflow, with lineage to `dataset_version` and `corpus_version`.
8. **Promote.** Manually. The LLM server hot-loads the adapter. Rollback switches the adapter version.

---

## 8. Security and privacy

- **In transit:** TLS at Traefik locally, service-to-service TLS in the cloud phase.
- **At rest:** object store encryption with keys from Vault. Postgres on an encrypted volume, with column encryption for free-text student questions (Vault Transit envelope keys).
- **RBAC roles:** `student`, `sme`, `expert`, `data_engineer`, `ml_engineer`, `ops`, `auditor`. Enforced in Postgres (roles and row-level security), in bucket policies, and behind Keycloak for Dagster, Grafana and MLflow.
- **Pseudonymization:** `pseudo_user = HMAC-SHA256(key_epoch, student_id)`, with the key in Vault. Free text is PII-scrubbed with Presidio before any fine-tuning or evaluation use.
- **Uploads:** student attachments are student data. They are encrypted, have a short TTL, are never sent outside the system and are never used for training.
- **External search:** allowlisted domains only, `robots.txt` respected, rate limits honoured, PII-stripped queries, licence recorded, content cleaned and scanned before W8 sees it, answers labelled "unvetted external source".
- **Code sandbox:** a separate container on an internal network with no internet access. Non-root, read-only root filesystem, temporary work directory, CPU, memory and wall-clock limits, one job per process.
- **Retention:** each table has a TTL enforced by a Dagster sweep. Iceberg snapshots older than the TTL **must be expired**, otherwise time travel keeps deleted rows alive. Pseudonym key epochs are destroyed at expiry (crypto-shredding).
- **Fail closed:** if Vault is unavailable, the gateway rejects requests rather than logging raw IDs.

---

## 9. Data contracts

Contracts live in `libs/contracts` (Pydantic v2). JSON Schema is exported from it and CI checks backward compatibility. Every record carries `schema_version`, the producer worker plus its image digest, and `ingestion_run_id` (offline) or `request_id` (online).

Each entry reads: **contract** (producer → consumer): key fields. A pair like `A / B` means request fields / response fields.

- **`DocumentVersion`** (upload → platform, W1 adds page_count): doc_id, doc_version, sha256, source_type (`textbook`, `lecture_note`, `past_exam`, `answer_key`, `external_exercise`), course_code, source_id, raw_uri, licence, source_url, page_count, supersedes.
- **`Region`** (W1 → W2, W3, W4, W5): region_id, doc_version, page_no, bbox, kind, raw_text, image_uri.
- **`ExtractedRegion`** (W2, W3, W4 → W5): region_id, kind, content (markdown, LaTeX or code), extractor name and version, confidence.
- **`CleanPage`** (W5 → W6, one per page): doc_version, page_no, markdown, region_ids, flags (min_ocr_conf, pii_hits, pii_remaining, dup_of, injection_hits).
- **`ChunkSet`** (W6 → quality gate, one per document version and run): doc_version, embedding_model, chunker_version, and chunks with chunk_id, doc_version, page_start, page_end, section_path, text, kinds, token_count, region_ids, embedding.
- **`CorpusManifest`** (quality gate → serving): version_id, parent_version, doc_versions, embedding_model, chunker_version, status, gate_report_id.
- **`AskRequest`** (gateway → orchestrator): request_id, pseudo_user, question, attachments.
- **`Attachment`** (gateway → orchestrator): attachment_id, request_id, media_type, uri, sha256, size_bytes.
- **`VisionRequest` / `VisionResult`** (orchestrator ↔ W2): attachment / text, latex, detected_kind, confidence.
- **`CleanRequest` / `CleanResult`** (orchestrator and W7 ↔ W5): text, origin (`question`, `upload`, `external`) / text, pii_hits, injection_hits, dropped.
- **`EmbedRequest` / `EmbedResult`** (orchestrator ↔ W6): texts, corpus_version / vectors, embedding_model.
- **`RetrievalRequest` / `RetrievalResult`** (orchestrator ↔ W7): request_id, question, query_vector, corpus_version, k, filters / chunks with chunk_id, dense, lexical, rerank, doc_version, page, plus sufficiency and timings.
- **`ExternalSearchRequest` / `ExternalSearchResult`** (orchestrator ↔ W7): request_id, query (PII-stripped), topics, max_results / items with url, title, snippet, licence, snapshot_uri, score, plus timings.
- **`ExternalCandidate`** (W7 → platform): candidate_id, url, snapshot_sha256, licence, course_code, topic, found_by (`answer_time` or `enrichment`), status.
- **`GenerationRequest` / `GenerationResult`** (orchestrator ↔ W8): request_id, question, contexts, external_contexts, model_version, prompt_version / answer, citations (chunk_id or url, doc_version, page), tool_calls, tokens, timings.
- **`CalcCheck` / `CalcResult`** (W8 → W4): operation, expression, variables, units / value, valid, explanation.
- **`CodeTask` / `CodeResult`** (W8 → W3): language (`r`, `python`, `excel`), task, data_uri, expected / code, stdout, values, verdict, duration_ms.
- **`EscalationTicket`** (orchestrator → escalation): ticket_id, request_id, pseudo_user, question, context_ids, confidence, external_results, status, expert, timestamps.
- **`StreamEvent`** (orchestrator → gateway → student, server-sent events): type (`answer.delta`, `answer.final`, `status.external_search`, `status.expert_pending`, `answer.expert`, `error`), text, citations, level.

The HTTP path of every online endpoint, with its request and response record, is defined once in `chatbot_contracts.routes`. `chatbot_contracts.samples` has a valid sample of every record for tests.

---

## 10. Failure modes

Each entry reads: **failure**, then what happens, how we detect it, and how we handle it.

- **GPU out of memory or LLM server crash**
  Effect: no answers. Detected by: health check, error-rate alert. Handled by: restart policy. The gateway returns 503 with retry-after. CPU fallback only when flagged as degraded.
- **More than 10 concurrent users**
  Effect: latency breach. Detected by: latency p95 alert. Handled by: continuous batching, admission queue, streaming.
- **Retrieval finds nothing relevant**
  Effect: risk of hallucination. Detected by: low sufficiency, low confidence. Handled by: external search, then the expert. Never answer without citations.
- **W8 cites a chunk it did not retrieve**
  Effect: fabricated citation. Detected by: citation validator. Handled by: strip or regenerate, lower confidence.
- **A bad document passes (OCR garbage)**
  Effect: wrong answers. Detected by: gate checks, SME sample, RAGAs drop. Handled by: move `serving` back to the previous version.
- **A correction arrives after answers cited the old page**
  Effect: stale citation. Detected by: lineage sweep. Handled by: flag affected answers, open an SME ticket.
- **Query encoder differs from the index's embedding model**
  Effect: nonsense retrieval. Detected by: version check in W6 and W7. Handled by: refuse and alert.
- **A pipeline worker fails mid-run**
  Effect: partial candidate. Detected by: Dagster run status. Handled by: retries. A candidate without a complete manifest can never publish.
- **Instructions hidden in sources or web pages**
  Effect: the model follows injected text. Detected by: W5 injection scan, guard on retrieved chunks. Handled by: quarantine the region or page. Sources stay in a separate data role in the prompt.
- **External search down or rate-limited**
  Effect: escalation delay. Detected by: timeout. Handled by: skip to the expert. NCBI allows 3 requests per second without a key and 10 with one.
- **Generated code misbehaves (loop, fork, large output)**
  Effect: resource exhaustion. Detected by: sandbox limits. Handled by: kill on limit, return verdict `error`, W8 answers without the code result.
- **Unreadable student photo**
  Effect: wrong question text. Detected by: W2 confidence. Handled by: ask the student to retype or retake the photo.
- **No expert on duty**
  Effect: the ticket waits. Detected by: rota coverage check, response-time timer. Handled by: fall back to the course coordinator and tell the student the expected wait.
- **RAGAs judge drift**
  Effect: misleading scores. Detected by: calibration set. Handled by: recalibrate. The judge version is stored on every score.
- **Vault unavailable**
  Effect: cannot pseudonymize. Detected by: health check. Handled by: fail closed.
- **Retention sweep fails**
  Effect: data kept too long. Detected by: sweep job alert, audit. Handled by: re-run. Snapshot expiry is part of the same job.

---

## 11. Constraint conflicts (still open)

1. **Free-tier budget vs. self-hosted inference for 10 concurrent users.** No GPU instance is free-tier eligible. Locally, this becomes a hardware requirement for load tests only.
2. **External sources vs. the quality gate.** Resolved. External content is used at answer time only with an "unvetted" label, and enters the corpus only through the gate with SME sign-off.
3. **RAGAs "on an ongoing basis" vs. a self-hosted judge and latency.** Context recall needs reference answers, so it runs on the golden set. Live traffic gets reference-free metrics, sampled and off-peak.
4. **Retention limits vs. a reproducible fine-tuning dataset.** Decision needed. Options:
   - (a) SME-written and synthetic data only
   - (b) reproducible only within the retention window
   - (c) irreversible anonymization before a row enters a dataset
5. **Per-worker GPU metrics on a shared GPU.** Memory per process is exact. Utilization per process is only sampled.
6. **Vision and code on the answer path vs. latency on CPU.** A vision-language model and sandboxed R add seconds per request on CPU. The latency thresholds (Appendix D, still TBD) must be measured with and without attachments.

## 12. Assumptions to confirm

- Latency, response time, throughput and RAGAs thresholds (Appendix D, still TBD).
- "Photographed problem sets" means student uploads at answer time.
- The student frontend can upload attachments, show SSE status events and fetch late expert answers.
- The external domain allowlist needs Institution approval before M6.
- SME approvals and expert answers are backend APIs plus email, with no new UI.

---

## 13. Repository map

```
AI-chatbot/
  README.md, pyproject.toml, uv.lock, compose.yaml, .env.example
  docs/
    TECH_STACK.md
    architecture/              this file and diagrams/
  libs/
    contracts/                 chatbot_contracts: records, routes, samples, JSON schemas
    platform/                  chatbot_platform: storage, registry, index, lake, versioning, gate, lineage, retention
    common/                    chatbot_common: app factory, contract client, test fakes, model clients
  services/
    gateway/                   chatbot_gateway
    orchestrator/              chatbot_orchestrator
    escalation/                chatbot_escalation
  workers/
    w1_ingest/   w2_vision/   w3_code/ (with sandbox/)   w4_math/
    w5_clean/    w6_embed/    w7_deepsearch/             w8_gen/
  pipelines/                   chatbot_pipelines: Dagster code location
  ml/
    eval/                      chatbot_eval: golden set, RAGAs, gate checks, test runs
    finetune/                  chatbot_finetune: dataset, approval, QLoRA, registry
  infra/
    docker/                    one Dockerfile for every Python package
    local/                     config for Postgres, SeaweedFS, Keycloak, Traefik, SearXNG, Dagster, OTel, Grafana
    aws/terraform/             phase 2
  scripts/                     comment rule, lane boundaries, test runner
  tests/                       tests across packages
```

Services, workers, pipelines and ml packages depend only on the three libraries. They talk to each other over HTTP with the contracts, never through imports. `scripts/check_boundaries.py` enforces this in CI.
