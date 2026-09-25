"""Iceberg tables of the lake, the cleaned and chunked tiers plus every history table.

Locally the PyIceberg SQL catalog lives in Postgres, or in SQLite for tests. On AWS the Glue catalog
replaces it without changing callers, see aws.py. Corpus tables mirror a contract record field by
field, so records can be written with append_records and read back with read_records.
"""

from collections import defaultdict
from collections.abc import Collection, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
from pydantic import BaseModel
from pyiceberg.catalog import Catalog
from pyiceberg.catalog.sql import SqlCatalog
from pyiceberg.expressions import AlwaysTrue, In, LessThan

from chatbot_contracts.corpus import Chunk, ChunkSet, CleanPage
from chatbot_platform.settings import PlatformSettings

_STR = pa.string()
_INT = pa.int64()
_FLOAT = pa.float64()
_BOOL = pa.bool_()
_TS = pa.timestamp("us", tz="UTC")
_STRINGS = pa.list_(pa.string())

_RECORD = [("schema_version", _STR), ("producer", _STR)]
_OFFLINE = [*_RECORD, ("ingestion_run_id", _STR)]

TABLES: dict[str, pa.Schema] = {
    "corpus.regions": pa.schema(
        [
            *_OFFLINE,
            ("region_id", _STR),
            ("doc_version", _STR),
            ("page_no", _INT),
            ("kind", _STR),
            ("bbox", pa.list_(_FLOAT)),
            ("raw_text", _STR),
            ("image_uri", _STR),
        ]
    ),
    "corpus.extracted_regions": pa.schema(
        [
            *_OFFLINE,
            ("region_id", _STR),
            ("kind", _STR),
            ("content", _STR),
            ("extractor", pa.struct([("name", _STR), ("version", _STR)])),
            ("confidence", _FLOAT),
        ]
    ),
    "corpus.cleaned_pages": pa.schema(
        [
            *_OFFLINE,
            ("doc_version", _STR),
            ("page_no", _INT),
            ("markdown", _STR),
            ("region_ids", _STRINGS),
            (
                "flags",
                pa.struct(
                    [
                        ("min_ocr_conf", _FLOAT),
                        ("pii_hits", _INT),
                        ("pii_remaining", _INT),
                        ("dup_of", _STR),
                        ("injection_hits", _INT),
                    ]
                ),
            ),
        ]
    ),
    "corpus.chunks": pa.schema(
        [
            *_OFFLINE,
            ("doc_version", _STR),
            ("embedding_model", _STR),
            ("chunker_version", _STR),
            ("chunk_id", _STR),
            ("page_start", _INT),
            ("page_end", _INT),
            ("section_path", _STRINGS),
            ("text", _STR),
            ("kinds", _STRINGS),
            ("token_count", _INT),
            ("region_ids", _STRINGS),
            ("embedding", pa.list_(pa.float32())),
        ]
    ),
    "external.candidates": pa.schema(
        [
            ("candidate_id", _STR),
            ("url", _STR),
            ("snapshot_sha256", _STR),
            ("found_by", _STR),
            ("status", _STR),
            ("licence", _STR),
            ("course_code", _STR),
            ("topic", _STR),
            ("decided_by", _STR),
            ("created_at", _TS),
            ("decided_at", _TS),
        ]
    ),
    "external.fetches": pa.schema(
        [
            ("fetch_id", _STR),
            ("url", _STR),
            ("status_code", _INT),
            ("snapshot_sha256", _STR),
            ("licence", _STR),
            ("fetched_at", _TS),
        ]
    ),
    "interactions.requests": pa.schema(
        [
            ("request_id", _STR),
            ("pseudo_user", _STR),
            ("corpus_version", _INT),
            ("model_version", _STR),
            ("prompt_version", _STR),
            ("confidence", _FLOAT),
            ("level", _STR),
            ("used_external", _BOOL),
            ("escalated", _BOOL),
            ("source_corrected", _BOOL),
            ("ts", _TS),
        ]
    ),
    "interactions.citations": pa.schema(
        [
            ("request_id", _STR),
            ("chunk_id", _STR),
            ("url", _STR),
            ("doc_version", _STR),
            ("page", _INT),
            ("ts", _TS),
        ]
    ),
    "interactions.tool_calls": pa.schema(
        [
            ("request_id", _STR),
            ("tool", _STR),
            ("operation", _STR),
            ("language", _STR),
            ("duration_ms", _FLOAT),
            ("verdict", _STR),
            ("error", _STR),
            ("ts", _TS),
        ]
    ),
    "eval.ragas_scores": pa.schema(
        [
            ("run_id", _STR),
            ("ts", _TS),
            ("corpus_version", _INT),
            ("model_version", _STR),
            ("prompt_version", _STR),
            ("dataset", _STR),
            ("item_id", _STR),
            ("metric", _STR),
            ("score", _FLOAT),
            ("judge_model", _STR),
        ]
    ),
    "eval.test_cases": pa.schema(
        [
            ("case_id", _STR),
            ("level", _INT),
            ("question", _STR),
            ("source", _STR),
            ("reference_answer", _STR),
            ("course_code", _STR),
            ("topic", _STR),
        ]
    ),
    "eval.test_runs": pa.schema(
        [
            ("run_id", _STR),
            ("case_id", _STR),
            ("ts", _TS),
            ("response", _STR),
            ("level_reached", _STR),
            ("confidence", _FLOAT),
            ("escalated", _BOOL),
            ("ragas", pa.map_(_STR, _FLOAT)),
            ("remediation", _STR),
        ]
    ),
    "obs.request_facts": pa.schema(
        [
            ("request_id", _STR),
            ("ts", _TS),
            ("pseudo_user", _STR),
            ("corpus_version", _INT),
            ("model_version", _STR),
            ("prompt_version", _STR),
            ("latency_ms", _FLOAT),
            ("e2e_ms", _FLOAT),
            ("tokens_in", _INT),
            ("tokens_out", _INT),
            ("confidence", _FLOAT),
            ("level", _STR),
            ("guard_verdict", _STR),
            ("used_external", _BOOL),
            ("escalated", _BOOL),
            ("attachment_count", _INT),
        ]
    ),
    "obs.worker_resources": pa.schema(
        [
            ("ts", _TS),
            ("worker", _STR),
            ("role", _STR),
            ("container", _STR),
            ("cpu_pct", _FLOAT),
            ("mem_bytes", _INT),
            ("gpu_mem_bytes", _INT),
            ("gpu_util_pct", _FLOAT),
        ]
    ),
    "obs.guard_events": pa.schema(
        [
            ("ts", _TS),
            ("request_id", _STR),
            ("detector", _STR),
            ("stage", _STR),
            ("category", _STR),
            ("score", _FLOAT),
            ("action", _STR),
        ]
    ),
    "escalation.tickets": pa.schema(
        [
            ("ticket_id", _STR),
            ("request_id", _STR),
            ("pseudo_user", _STR),
            ("confidence", _FLOAT),
            ("status", _STR),
            ("context_ids", _STRINGS),
            ("external_urls", _STRINGS),
            ("external_response_ms", _FLOAT),
            ("expert", _STR),
            ("created_at", _TS),
            ("answered_at", _TS),
        ]
    ),
    "ft.datasets": pa.schema(
        [
            ("dataset_version", _STR),
            ("created_at", _TS),
            ("item_count", _INT),
            ("manifest_sha256", _STR),
            ("status", _STR),
            ("approved_by", _STR),
            ("approved_at", _TS),
        ]
    ),
    "ft.items": pa.schema(
        [
            ("item_id", _STR),
            ("dataset_version", _STR),
            ("split", _STR),
            ("course_code", _STR),
            ("topic", _STR),
            ("question", _STR),
            ("answer", _STR),
            ("source", _STR),
        ]
    ),
    "gate.reports": pa.schema(
        [
            ("report_id", _STR),
            ("version_id", _INT),
            ("created_at", _TS),
            ("auto_passed", _BOOL),
            ("requires_sme", _BOOL),
            ("sme_decision", _STR),
            ("failed_checks", _STRINGS),
        ]
    ),
}

TTL_COLUMNS: dict[str, str] = {
    "interactions.requests": "ts",
    "interactions.citations": "ts",
    "interactions.tool_calls": "ts",
    "obs.request_facts": "ts",
    "obs.worker_resources": "ts",
    "obs.guard_events": "ts",
    "escalation.tickets": "created_at",
}
"""History tables with a retention limit and the timestamp column the sweep filters on."""


def warehouse_location(location: str) -> str:
    """Folders become absolute plain paths. PyIceberg mishandles file uris with a Windows drive."""
    return location if "://" in location else str(Path(location).resolve())


def open_catalog(settings: PlatformSettings) -> Catalog:
    properties = {
        "uri": settings.iceberg_catalog_uri,
        "warehouse": warehouse_location(settings.warehouse),
    }
    if properties["warehouse"].startswith("s3://"):
        properties |= {
            "s3.endpoint": settings.s3_endpoint_url or "",
            "s3.access-key-id": settings.s3_access_key,
            "s3.secret-access-key": settings.s3_secret_key.get_secret_value(),
            "s3.region": settings.s3_region,
        }
    return SqlCatalog("chatbot", **properties)


def ensure_tables(catalog: Catalog) -> list[str]:
    """Create every namespace and table that does not exist yet. Safe to repeat."""
    for identifier, schema in TABLES.items():
        catalog.create_namespace_if_not_exists(identifier.split(".")[0])
        catalog.create_table_if_not_exists(identifier, schema=schema)
    return list(TABLES)


def append_rows(catalog: Catalog, table: str, rows: Sequence[dict[str, Any]]) -> int:
    if not rows:
        return 0
    arrow = pa.Table.from_pylist(list(rows), schema=TABLES[table])
    catalog.load_table(table).append(arrow)
    return arrow.num_rows


def append_records(catalog: Catalog, table: str, records: Sequence[BaseModel]) -> int:
    """Write records whose fields match the table columns, such as Region or CleanPage."""
    return append_rows(catalog, table, [record.model_dump() for record in records])


def read_rows(
    catalog: Catalog, table: str, run_ids: Collection[str] | None = None
) -> list[dict[str, Any]]:
    """All rows, or only the rows of the given ingestion runs."""
    if run_ids is not None and not run_ids:
        return []
    row_filter = AlwaysTrue() if run_ids is None else In("ingestion_run_id", set(run_ids))
    return catalog.load_table(table).scan(row_filter=row_filter).to_arrow().to_pylist()


def read_records[M: BaseModel](
    catalog: Catalog, table: str, model: type[M], run_ids: Collection[str] | None = None
) -> list[M]:
    return [model.model_validate(row) for row in read_rows(catalog, table, run_ids)]


def write_chunk_set(catalog: Catalog, chunk_set: ChunkSet) -> int:
    header = chunk_set.model_dump(exclude={"chunks"})
    return append_rows(
        catalog, "corpus.chunks", [header | chunk.model_dump() for chunk in chunk_set.chunks]
    )


def read_chunk_sets(catalog: Catalog, run_ids: Collection[str]) -> list[ChunkSet]:
    """Rebuild one ChunkSet per ingestion run and document version."""
    header_fields = set(ChunkSet.model_fields) - {"chunks"}
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in read_rows(catalog, "corpus.chunks", run_ids):
        groups[(row["ingestion_run_id"], row["doc_version"])].append(row)
    chunk_sets = []
    for rows in groups.values():
        rows.sort(key=lambda row: (row["page_start"], row["chunk_id"]))
        chunks = [Chunk(**{name: row[name] for name in Chunk.model_fields}) for row in rows]
        header = {name: rows[0][name] for name in header_fields}
        chunk_sets.append(ChunkSet(**header, chunks=chunks))
    return chunk_sets


def read_clean_pages(catalog: Catalog, run_ids: Collection[str]) -> list[CleanPage]:
    return read_records(catalog, "corpus.cleaned_pages", CleanPage, run_ids)


def delete_older_than(catalog: Catalog, table: str, column: str, cutoff: datetime) -> int:
    """Delete rows older than cutoff and return how many were deleted."""
    iceberg_table = catalog.load_table(table)
    row_filter = LessThan(column, cutoff.isoformat())
    doomed = iceberg_table.scan(row_filter=row_filter).count()
    if doomed:
        iceberg_table.delete(delete_filter=row_filter)
    return doomed


def expire_snapshots(catalog: Catalog, table: str, cutoff: datetime) -> None:
    """Drop snapshots older than cutoff. Without this, time travel keeps deleted rows alive."""
    catalog.load_table(table).maintenance.expire_snapshots().older_than(cutoff).commit()
