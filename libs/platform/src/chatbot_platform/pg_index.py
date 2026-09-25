"""Serving index on Postgres with pgvector for dense search and tsvector for full text search.

Live search uses the HNSW index, which is approximate. Audit replays should call search_dense with
exact set to True, which disables the index scan for that transaction.
"""

from collections.abc import Collection, Sequence

from sqlalchemy import Engine, and_, func, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert

from chatbot_contracts.corpus import Chunk, ChunkSet
from chatbot_platform.models import IndexHit, StoredChunk
from chatbot_platform.sql import serving_tables

_CONTENT_COLUMNS = (
    "chunk_id",
    "doc_version",
    "page_start",
    "page_end",
    "section_path",
    "text",
    "kinds",
    "token_count",
    "region_ids",
    "ingestion_run_id",
    "embedding_model",
    "chunker_version",
)


class PgServingIndex:
    def __init__(self, engine: Engine, embedding_dim: int) -> None:
        self.engine = engine
        self.embedding_dim = embedding_dim
        self.tables = serving_tables(embedding_dim)

    def add_chunk_set(self, chunk_set: ChunkSet) -> None:
        rows = []
        for chunk in chunk_set.chunks:
            if chunk.embedding is None or len(chunk.embedding) != self.embedding_dim:
                raise ValueError(
                    f"chunk {chunk.chunk_id} needs a {self.embedding_dim} dim embedding"
                )
            row = chunk.model_dump(mode="json")
            row.update(
                ingestion_run_id=chunk_set.ingestion_run_id,
                embedding_model=chunk_set.embedding_model,
                chunker_version=chunk_set.chunker_version,
            )
            rows.append(row)
        if not rows:
            return
        statement = insert(self.tables.chunks).on_conflict_do_nothing(index_elements=["chunk_id"])
        with self.engine.begin() as conn:
            conn.execute(statement, rows)

    def open_intervals(self, chunk_ids: Collection[str], version: int) -> None:
        if not chunk_ids:
            return
        rows = [{"chunk_id": chunk_id, "valid_from_version": version} for chunk_id in chunk_ids]
        statement = insert(self.tables.validity).on_conflict_do_nothing()
        with self.engine.begin() as conn:
            conn.execute(statement, rows)

    def close_intervals(self, chunk_ids: Collection[str], version: int) -> None:
        if not chunk_ids:
            return
        validity = self.tables.validity
        statement = (
            update(validity)
            .where(
                validity.c.chunk_id.in_(list(chunk_ids)),
                validity.c.valid_to_version.is_(None),
                validity.c.valid_from_version < version,
            )
            .values(valid_to_version=version)
        )
        with self.engine.begin() as conn:
            conn.execute(statement)

    def _visible_at(self, version: int):
        validity = self.tables.validity
        return and_(
            validity.c.valid_from_version <= version,
            or_(validity.c.valid_to_version.is_(None), validity.c.valid_to_version > version),
        )

    def _joined(self):
        chunks, validity = self.tables.chunks, self.tables.validity
        return chunks.join(validity, chunks.c.chunk_id == validity.c.chunk_id)

    def active_chunks(self, version: int) -> dict[str, str]:
        chunks = self.tables.chunks
        query = (
            select(chunks.c.chunk_id, chunks.c.doc_version)
            .select_from(self._joined())
            .where(self._visible_at(version))
        )
        with self.engine.connect() as conn:
            return {chunk_id: doc_version for chunk_id, doc_version in conn.execute(query)}

    def get_chunks(self, chunk_ids: Collection[str]) -> list[StoredChunk]:
        chunks = self.tables.chunks
        columns = [chunks.c[name] for name in _CONTENT_COLUMNS]
        query = select(*columns).where(chunks.c.chunk_id.in_(list(chunk_ids)))
        with self.engine.connect() as conn:
            return [_stored(row) for row in conn.execute(query).mappings()]

    def search_dense(
        self, vector: Sequence[float], version: int, k: int, exact: bool = False
    ) -> list[IndexHit]:
        chunks = self.tables.chunks
        distance = chunks.c.embedding.cosine_distance(list(vector))
        columns = [chunks.c[name] for name in _CONTENT_COLUMNS]
        query = (
            select(*columns, (1 - distance).label("score"))
            .select_from(self._joined())
            .where(self._visible_at(version))
            .order_by(distance)
            .limit(k)
        )
        with self.engine.begin() as conn:
            if exact:
                conn.execute(text("SET LOCAL enable_indexscan = off"))
            rows = conn.execute(query).mappings().all()
        return [IndexHit(chunk=_stored(row), score=float(row["score"])) for row in rows]

    def search_lexical(self, query_text: str, version: int, k: int) -> list[IndexHit]:
        chunks = self.tables.chunks
        tsquery = func.plainto_tsquery("english", query_text)
        rank = func.ts_rank_cd(chunks.c.tsv, tsquery)
        columns = [chunks.c[name] for name in _CONTENT_COLUMNS]
        query = (
            select(*columns, rank.label("score"))
            .select_from(self._joined())
            .where(self._visible_at(version), chunks.c.tsv.op("@@")(tsquery))
            .order_by(rank.desc())
            .limit(k)
        )
        with self.engine.connect() as conn:
            rows = conn.execute(query).mappings().all()
        return [IndexHit(chunk=_stored(row), score=float(row["score"])) for row in rows]


def _stored(row) -> StoredChunk:
    chunk_fields = set(Chunk.model_fields) - {"embedding"}
    return StoredChunk(
        chunk=Chunk(**{name: row[name] for name in chunk_fields}),
        ingestion_run_id=row["ingestion_run_id"],
        embedding_model=row["embedding_model"],
        chunker_version=row["chunker_version"],
    )
