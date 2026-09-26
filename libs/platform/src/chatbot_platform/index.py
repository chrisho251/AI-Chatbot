"""Serving index port and an in memory adapter for tests.

Chunk content is stored once. Validity intervals say which knowledge base versions see a chunk,
so a query at version v only sees chunks with valid_from_version at or below v and valid_to_version
above v.
A chunk can have several intervals when a rollback is followed by a new publish.
"""

import math
import re
from collections.abc import Collection, Sequence
from typing import Protocol

from chatbot_contracts.knowledge_base import ChunkSet
from chatbot_platform.models import IndexHit, StoredChunk


class ServingIndex(Protocol):
    def add_chunk_set(self, chunk_set: ChunkSet) -> None:
        """Store chunk content and embeddings. Chunks already stored are left unchanged."""
        ...

    def open_intervals(self, chunk_ids: Collection[str], version: int) -> None:
        """Make the chunks visible from version onward. Safe to repeat."""
        ...

    def close_intervals(self, chunk_ids: Collection[str], version: int) -> None:
        """Hide the chunks from version onward. Safe to repeat."""
        ...

    def active_chunks(self, version: int) -> dict[str, str]:
        """Chunk id to doc version for every chunk visible at version."""
        ...

    def get_chunks(self, chunk_ids: Collection[str]) -> list[StoredChunk]: ...

    def search_dense(self, vector: Sequence[float], version: int, k: int) -> list[IndexHit]:
        """Nearest chunks by cosine similarity, best first."""
        ...

    def search_lexical(self, query_text: str, version: int, k: int) -> list[IndexHit]:
        """Best full text matches, best first."""
        ...


def _visible(intervals: list[tuple[int, int | None]], version: int) -> bool:
    return any(start <= version and (end is None or end > version) for start, end in intervals)


def _terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norm = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return dot / norm if norm else 0.0


class InMemoryServingIndex:
    """Same behaviour as the Postgres index with naive scoring. Lexical score is term overlap."""

    def __init__(self) -> None:
        self._chunks: dict[str, StoredChunk] = {}
        self._embeddings: dict[str, list[float]] = {}
        self._intervals: dict[str, list[tuple[int, int | None]]] = {}

    def add_chunk_set(self, chunk_set: ChunkSet) -> None:
        for chunk in chunk_set.chunks:
            if chunk.chunk_id in self._chunks:
                continue
            if chunk.embedding is None:
                raise ValueError(f"chunk {chunk.chunk_id} has no embedding")
            self._embeddings[chunk.chunk_id] = list(chunk.embedding)
            self._chunks[chunk.chunk_id] = StoredChunk(
                chunk=chunk.model_copy(update={"embedding": None}),
                ingestion_run_id=chunk_set.ingestion_run_id,
                embedding_model=chunk_set.embedding_model,
                chunker_version=chunk_set.chunker_version,
            )

    def open_intervals(self, chunk_ids: Collection[str], version: int) -> None:
        for chunk_id in chunk_ids:
            if chunk_id not in self._chunks:
                raise KeyError(f"chunk {chunk_id} is not stored")
            intervals = self._intervals.setdefault(chunk_id, [])
            if all(start != version for start, _ in intervals):
                intervals.append((version, None))

    def close_intervals(self, chunk_ids: Collection[str], version: int) -> None:
        for chunk_id in chunk_ids:
            self._intervals[chunk_id] = [
                (start, version if end is None and start < version else end)
                for start, end in self._intervals.get(chunk_id, [])
            ]

    def active_chunks(self, version: int) -> dict[str, str]:
        return {
            chunk_id: self._chunks[chunk_id].chunk.doc_version
            for chunk_id, intervals in self._intervals.items()
            if _visible(intervals, version)
        }

    def get_chunks(self, chunk_ids: Collection[str]) -> list[StoredChunk]:
        return [self._chunks[chunk_id] for chunk_id in chunk_ids if chunk_id in self._chunks]

    def search_dense(self, vector: Sequence[float], version: int, k: int) -> list[IndexHit]:
        scored = [
            IndexHit(
                chunk=self._chunks[chunk_id], score=_cosine(vector, self._embeddings[chunk_id])
            )
            for chunk_id in self.active_chunks(version)
        ]
        return sorted(scored, key=lambda hit: hit.score, reverse=True)[:k]

    def search_lexical(self, query_text: str, version: int, k: int) -> list[IndexHit]:
        query = _terms(query_text)
        if not query:
            return []
        scored = []
        for chunk_id in self.active_chunks(version):
            stored = self._chunks[chunk_id]
            overlap = len(query & _terms(stored.chunk.text)) / len(query)
            if overlap > 0:
                scored.append(IndexHit(chunk=stored, score=overlap))
        return sorted(scored, key=lambda hit: hit.score, reverse=True)[:k]
