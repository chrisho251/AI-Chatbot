"""Rows of the ingest schema, the cleaned and chunked tiers that W1 to W6 write.

Each table mirrors a contract record field by field, so a record goes in with append_records and
comes back with read_records. Writing the same record twice keeps one row, so a step that Dagster
repeats after a failure is safe. The quality gate reads clean pages and chunk sets from here,
publish copies the chunk sets into serving.chunks, and retention deletes old staged chunks.
"""

from collections import defaultdict
from collections.abc import Collection, Sequence
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Engine, Table, delete, insert, select, tuple_

from chatbot_contracts.knowledge_base import Chunk, ChunkSet, CleanPage
from chatbot_platform import sql

TABLES: dict[str, Table] = {
    "ingest.regions": sql.regions,
    "ingest.extracted_regions": sql.extracted_regions,
    "ingest.cleaned_pages": sql.cleaned_pages,
    "ingest.chunks": sql.staged_chunks,
}


def _write(engine: Engine, table: Table, rows: list[dict[str, Any]]) -> int:
    """Replace rows that share a primary key, then insert, in one transaction."""
    if not rows:
        return 0
    now = sql.utcnow()
    rows = [row | {"created_at": now} for row in rows]
    key = list(table.primary_key.columns)
    keys = [tuple(row[column.name] for column in key) for row in rows]
    with engine.begin() as conn:
        conn.execute(delete(table).where(tuple_(*key).in_(keys)))
        conn.execute(insert(table), rows)
    return len(rows)


def append_records(engine: Engine, table: str, records: Sequence[BaseModel]) -> int:
    """Write records whose fields match the table columns, such as Region or CleanPage."""
    return _write(engine, TABLES[table], [record.model_dump(mode="json") for record in records])


def read_rows(
    engine: Engine, table: str, run_ids: Collection[str] | None = None
) -> list[dict[str, Any]]:
    """All rows, or only the rows of the given ingestion runs, in primary key order."""
    if run_ids is not None and not run_ids:
        return []
    source = TABLES[table]
    query = select(source).order_by(*source.primary_key.columns)
    if run_ids is not None:
        query = query.where(source.c.ingestion_run_id.in_(list(run_ids)))
    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(query).mappings()]


def read_records[M: BaseModel](
    engine: Engine, table: str, model: type[M], run_ids: Collection[str] | None = None
) -> list[M]:
    fields = set(model.model_fields)
    return [
        model.model_validate({name: value for name, value in row.items() if name in fields})
        for row in read_rows(engine, table, run_ids)
    ]


def write_chunk_set(engine: Engine, chunk_set: ChunkSet) -> int:
    header = chunk_set.model_dump(mode="json", exclude={"chunks"})
    rows = [header | chunk.model_dump(mode="json") for chunk in chunk_set.chunks]
    return _write(engine, sql.staged_chunks, rows)


def read_chunk_sets(engine: Engine, run_ids: Collection[str]) -> list[ChunkSet]:
    """Rebuild one ChunkSet per ingestion run and document version."""
    header_fields = set(ChunkSet.model_fields) - {"chunks"}
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in read_rows(engine, "ingest.chunks", run_ids):
        groups[(row["ingestion_run_id"], row["doc_version"])].append(row)
    chunk_sets = []
    for rows in groups.values():
        rows.sort(key=lambda row: (row["page_start"], row["chunk_id"]))
        chunks = [Chunk(**{name: row[name] for name in Chunk.model_fields}) for row in rows]
        header = {name: rows[0][name] for name in header_fields}
        chunk_sets.append(ChunkSet(**header, chunks=chunks))
    return chunk_sets


def read_clean_pages(engine: Engine, run_ids: Collection[str]) -> list[CleanPage]:
    return read_records(engine, "ingest.cleaned_pages", CleanPage, run_ids)
