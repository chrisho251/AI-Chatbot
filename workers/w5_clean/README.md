# W5 clean

Worker-clean from Appendix A.4. Two roles in one image:

- **Offline (ingest):** joins regions into pages, normalizes, removes boilerplate, dedupes, scrubs PII, scans for injected instructions, writes the `cleaned` tier.
- **Online (answer time):** cleans the question, uploaded text and fetched web pages.

**Owner:** Lane B.
**Offline reads:** `corpus.regions` (text) and `corpus.extracted_regions`. **Writes:** `corpus.cleaned_pages`, exactly one `CleanPage` per page.
**Online endpoint:** `POST /v1/clean`, `CleanRequest` to `CleanResult`.

## Files

- `job.py`, `normalize.py`, `dedupe.py`, `pii.py`, `injection.py`: offline.
- `online.py`, `web.py`, `serve.py`: online.

## Setup note

Presidio needs a spaCy English model that is not on PyPI:

```bash
uv run --package chatbot-w5-clean python -m spacy download en_core_web_lg
```

The Dockerfile must do the same at build time.

## Start here

1. `normalize` and `pii`, pure functions with unit tests.
2. `job.run`, using sample regions written into `make_test_platform`. You do not need W1 to be finished.
3. `online.clean_text` and `web.extract_text`.
4. `injection` and `dedupe`.

## Test

```bash
uv run --package chatbot-w5-clean pytest workers/w5_clean/tests
```
