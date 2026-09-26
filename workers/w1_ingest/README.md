# W1 ingest

Worker-ingest from Appendix A.4. Offline only: it turns one registered document version into typed regions.

**Owner:** Lane B.
**Reads:** the registry (`DocumentVersion`) and the raw file in the object store.
**Writes:** `ingest.regions` (`Region` records) and the page count in the registry.
**Runs as:** `chatbot-w1-ingest-job --run-id <id> --doc-version <version>`, started by Dagster.

## Files

- `job.py`: the entrypoint. Implement `run`.
- `layout.py`: Docling layout analysis. Implement `analyze`.

## Start here

1. Implement `layout.analyze` against a fixture PDF.
2. Implement `job.run` with `chatbot_platform.testing.make_test_platform` in your test: upload the fixture with `register_document`, run the job, read `ingest.regions` back with `chatbot_platform.ingest.read_records`.

You never need the other lanes: W2 to W5 only read the rows you write, and the pipeline only calls your CLI.

## Test

```bash
uv run --package chatbot-w1-ingest pytest workers/w1_ingest/tests
```
