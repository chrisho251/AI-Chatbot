import pytest
from sqlalchemy import inspect

from chatbot_contracts import samples
from chatbot_contracts.knowledge_base import ExtractedRegion, Region
from chatbot_platform import ingest, sql


def test_every_ingest_table_exists(platform):
    schema = None if platform.engine.dialect.name == "sqlite" else sql.INGEST
    names = set(inspect(platform.engine).get_table_names(schema=schema))
    assert {table.name for table in ingest.TABLES.values()} <= names


def test_flat_records_round_trip(platform):
    region = samples.sample_region()
    extracted = samples.sample_extracted_region()
    ingest.append_records(platform.engine, "ingest.regions", [region])
    ingest.append_records(platform.engine, "ingest.extracted_regions", [extracted])
    assert ingest.read_records(platform.engine, "ingest.regions", Region) == [region]
    assert ingest.read_records(platform.engine, "ingest.extracted_regions", ExtractedRegion) == [
        extracted
    ]


def test_clean_pages_are_read_back_by_run(platform):
    pages = [samples.sample_clean_page(page_no=p) for p in (1, 2)]
    other = samples.sample_clean_page(ingestion_run_id="run-other")
    ingest.append_records(platform.engine, "ingest.cleaned_pages", [*pages, other])
    assert ingest.read_clean_pages(platform.engine, [samples.RUN_ID]) == pages
    assert ingest.read_clean_pages(platform.engine, []) == []


def test_writing_a_record_twice_keeps_one_row(platform):
    page = samples.sample_clean_page()
    ingest.append_records(platform.engine, "ingest.cleaned_pages", [page])
    edited = page.model_copy(update={"markdown": "Edited page."})
    ingest.append_records(platform.engine, "ingest.cleaned_pages", [edited])
    assert ingest.read_clean_pages(platform.engine, [samples.RUN_ID]) == [edited]


def test_chunk_sets_round_trip(platform):
    chunk_set = samples.sample_chunk_set()
    ingest.write_chunk_set(platform.engine, chunk_set)
    [restored] = ingest.read_chunk_sets(platform.engine, [samples.RUN_ID])
    assert restored.model_dump(exclude={"chunks"}) == chunk_set.model_dump(exclude={"chunks"})
    for got, want in zip(restored.chunks, chunk_set.chunks, strict=True):
        assert got.model_dump(exclude={"embedding"}) == want.model_dump(exclude={"embedding"})
        assert got.embedding == pytest.approx(want.embedding, rel=1e-9)
