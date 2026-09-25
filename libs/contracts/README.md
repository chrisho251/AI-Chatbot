# chatbot-contracts

The typed records every worker and service exchange. This package is the only thing two lanes share, so treat it as a public API.

**Owner:** Lane A, with review from every lane on any change.
**Depends on:** pydantic only.

## What is inside

- `base.py`: `Record`, `OfflineRecord` (carries `ingestion_run_id`), `OnlineRecord` (carries `request_id`). Every record has `schema_version` and `producer`.
- `enums.py`: closed sets of values, such as `SourceType`, `RegionKind`, `ConfidenceLevel`.
- `ids.py`: content-addressed ids: `make_doc_id`, `make_doc_version`, `make_chunk_id`.
- `corpus.py`: offline records, from `DocumentVersion` to `CorpusManifest`.
- `query.py`, `tools.py`, `external.py`, `escalation.py`: online records.
- `routes.py`: the HTTP endpoint of every online component, with its request and response record.
- `samples.py`: a valid sample of every record. Use these in tests instead of waiting for another lane.
- `schemas/`: exported JSON Schema, one file per record. Generated, do not edit by hand.

## Rules for changing a contract

1. Adding an optional field is safe. Renaming or removing a field, or making one required, breaks other lanes.
2. A breaking change needs a PR reviewed by every lane owner and a bump of `SCHEMA_VERSION`.
3. After any change, run `uv run poe export-schemas` and commit the files in `schemas/`.
4. Keep `samples.py` complete. A test fails when a record type has no sample.

## Test

```bash
uv run --package chatbot-contracts pytest libs/contracts/tests
```
