from datetime import UTC, datetime, timedelta

import pytest

from chatbot_contracts import samples
from chatbot_contracts.corpus import ExtractedRegion, Region
from chatbot_platform import lake


def test_every_table_exists(platform):
    names = {
        ".".join(identifier)
        for ns in platform.catalog.list_namespaces()
        for identifier in platform.catalog.list_tables(ns)
    }
    assert names == set(lake.TABLES)


def test_flat_records_round_trip(platform):
    region = samples.sample_region()
    extracted = samples.sample_extracted_region()
    lake.append_records(platform.catalog, "corpus.regions", [region])
    lake.append_records(platform.catalog, "corpus.extracted_regions", [extracted])
    assert lake.read_records(platform.catalog, "corpus.regions", Region) == [region]
    assert lake.read_records(platform.catalog, "corpus.extracted_regions", ExtractedRegion) == [
        extracted
    ]


def test_clean_pages_are_read_back_by_run(platform):
    pages = [samples.sample_clean_page(page_no=p) for p in (1, 2)]
    other = samples.sample_clean_page(ingestion_run_id="run-other")
    lake.append_records(platform.catalog, "corpus.cleaned_pages", [*pages, other])
    assert lake.read_clean_pages(platform.catalog, [samples.RUN_ID]) == pages
    assert lake.read_clean_pages(platform.catalog, []) == []


def test_chunk_sets_round_trip(platform):
    chunk_set = samples.sample_chunk_set()
    lake.write_chunk_set(platform.catalog, chunk_set)
    [restored] = lake.read_chunk_sets(platform.catalog, [samples.RUN_ID])
    assert restored.model_dump(exclude={"chunks"}) == chunk_set.model_dump(exclude={"chunks"})
    for got, want in zip(restored.chunks, chunk_set.chunks, strict=True):
        assert got.model_dump(exclude={"embedding"}) == want.model_dump(exclude={"embedding"})
        assert got.embedding == pytest.approx(want.embedding, rel=1e-6)


def test_delete_older_than_and_expire_snapshots(platform):
    now = datetime.now(UTC)
    rows = [
        {"ts": now - timedelta(days=900), "worker": "old"},
        {"ts": now, "worker": "new"},
    ]
    lake.append_rows(platform.catalog, "obs.worker_resources", rows)
    deleted = lake.delete_older_than(
        platform.catalog, "obs.worker_resources", "ts", now - timedelta(days=730)
    )
    lake.expire_snapshots(platform.catalog, "obs.worker_resources", datetime.now(UTC))
    table = platform.catalog.load_table("obs.worker_resources")
    assert deleted == 1
    assert [row["worker"] for row in table.scan().to_arrow().to_pylist()] == ["new"]
    assert len(table.snapshots()) == 1
