# W1 ingest

Worker-ingest from Appendix A.4. Offline only: it turns one registered document version into typed regions.

**Owner:** Lane B.
**Reads:** the registry (`DocumentVersion`) and the raw file in the object store.
**Writes:** `ingest.regions` (`Region` records) and the page count in the registry.
**Runs as:** `chatbot-w1-ingest-job --run-id <id> --doc-version <version>`, started by Dagster.

## Files

- `job.py`: the entrypoint. Loads the raw file, calls `layout.analyze`, writes the regions and
  sets the page count. It returns how many regions it wrote.
- `layout.py`: Docling layout analysis. Maps every Docling item to a `RegionKind`, keeps the box
  and the raw text of text, table and code regions, and stores the pictures of figure and scan
  regions in the raw bucket.
- `tests/fixtures/build_fixture.py`: regenerates the two test PDFs. Run it from the repository
  root with `uv run --package chatbot-w1-ingest python workers/w1_ingest/tests/fixtures/build_fixture.py`.

## Notes

OCR belongs to W2 and the code and formula models to W3 and W4, so layout runs the layout, table
and picture classification models only. A picture is a `scan` when the classifier says it covers a
whole page and a `figure` otherwise. Every page gets at least one region and a blank page gets one
empty text region, otherwise the page coverage check of the quality gate fails.

## Test

```bash
uv run --package chatbot-w1-ingest pytest workers/w1_ingest/tests
```

The first run downloads the Docling layout, table and picture classification models, so it needs
network access and a few minutes.
