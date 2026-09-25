# W7 deepsearch

Worker-deepsearch from Appendix A.4. **Internal first, external second.**

- **Internal (online):** hybrid search (pgvector dense and Postgres full-text) on the pinned corpus version, fused and reranked.
- **External (online):** searches allowlisted sources for exercises and answer keys when internal evidence is weak or the answer lands at L3. Results are labelled unvetted.
- **Enrichment (offline):** weekly search by course topic. Finds are queued for SME triage and only enter the corpus through the quality gate.

**Owner:** Lane C.
**Endpoints:** `POST /v1/retrieve` (`routes.RETRIEVE`) and `POST /v1/external` (`routes.EXTERNAL_SEARCH`).
**Enrichment CLI:** `chatbot-w7-enrichment-job --course "STAT 101" --topic "confidence intervals"`.

## Files

- `internal.py`, `fusion.py`: internal retrieval.
- `external.py`, `allowlist.py`, `candidates.py`, `sources/`: external search.
- `job.py`: enrichment.

## Start here

1. `fusion.reciprocal_rank`, then `internal.retrieve` against `make_test_platform` with published sample chunks.
2. `sources/searxng.py` and `external.search_external` with every source faked.
3. `candidates.queue` and `job.run`.

## Test

```bash
uv run --package chatbot-w7-deepsearch pytest workers/w7_deepsearch/tests
```
