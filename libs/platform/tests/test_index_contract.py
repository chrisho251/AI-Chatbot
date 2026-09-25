"""Behaviour every ServingIndex must have. Postgres runs only with the integration marker."""

import pytest

from chatbot_contracts import samples
from chatbot_platform.index import InMemoryServingIndex
from chatbot_platform.pg_index import PgServingIndex


@pytest.fixture(params=["memory", pytest.param("postgres", marks=pytest.mark.integration)])
def index(request):
    if request.param == "memory":
        return InMemoryServingIndex()
    return PgServingIndex(request.getfixturevalue("pg_engine"), samples.EMBEDDING_DIM)


@pytest.fixture
def chunk_set():
    return samples.sample_chunk_set()


def _ids(chunk_set):
    return [chunk.chunk_id for chunk in chunk_set.chunks]


def test_chunks_are_visible_only_inside_their_interval(index, chunk_set):
    first, second, third = _ids(chunk_set)
    index.add_chunk_set(chunk_set)
    index.open_intervals([first, second], 1)
    index.close_intervals([first], 2)
    index.open_intervals([third], 2)
    assert set(index.active_chunks(1)) == {first, second}
    assert set(index.active_chunks(2)) == {second, third}
    assert set(index.active_chunks(5)) == {second, third}


def test_open_and_close_are_safe_to_repeat(index, chunk_set):
    first, _, _ = _ids(chunk_set)
    index.add_chunk_set(chunk_set)
    index.add_chunk_set(chunk_set)
    index.open_intervals([first], 1)
    index.open_intervals([first], 1)
    index.close_intervals([first], 3)
    index.close_intervals([first], 3)
    assert set(index.active_chunks(2)) == {first}
    assert index.active_chunks(3) == {}


def test_a_chunk_can_come_back_after_a_rollback(index, chunk_set):
    first, second, third = _ids(chunk_set)
    index.add_chunk_set(chunk_set)
    index.open_intervals([first, second], 1)
    index.close_intervals([first], 2)
    index.open_intervals([third], 2)
    index.close_intervals([third], 3)
    index.open_intervals([first], 3)
    assert set(index.active_chunks(1)) == {first, second}
    assert set(index.active_chunks(2)) == {second, third}
    assert set(index.active_chunks(3)) == {first, second}


def test_dense_search_ranks_the_closest_chunk_first(index, chunk_set):
    index.add_chunk_set(chunk_set)
    index.open_intervals(_ids(chunk_set), 1)
    target = chunk_set.chunks[1]
    hits = index.search_dense(target.embedding, 1, k=2)
    assert hits[0].chunk.chunk.chunk_id == target.chunk_id
    assert hits[0].score == pytest.approx(1.0, abs=1e-5)
    assert len(hits) == 2


def test_lexical_search_finds_matching_terms(index, chunk_set):
    index.add_chunk_set(chunk_set)
    index.open_intervals(_ids(chunk_set), 1)
    hits = index.search_lexical("odds ratio", 1, k=3)
    assert hits[0].chunk.chunk.text == samples.PAGE_TEXTS[2]


def test_search_ignores_chunks_outside_the_version(index, chunk_set):
    first, second, third = _ids(chunk_set)
    index.add_chunk_set(chunk_set)
    index.open_intervals([first], 1)
    hits = index.search_dense(chunk_set.chunks[2].embedding, 1, k=3)
    assert [hit.chunk.chunk.chunk_id for hit in hits] == [first]


def test_get_chunks_returns_lineage_without_embedding(index, chunk_set):
    index.add_chunk_set(chunk_set)
    stored = index.get_chunks([chunk_set.chunks[0].chunk_id])[0]
    assert stored.ingestion_run_id == chunk_set.ingestion_run_id
    assert stored.embedding_model == chunk_set.embedding_model
    assert stored.chunk.embedding is None
    assert stored.chunk.text == chunk_set.chunks[0].text
