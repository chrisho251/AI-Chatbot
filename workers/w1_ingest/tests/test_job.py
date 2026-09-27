"""The W1 job end to end against the test platform, SQLite and a local object store."""

from pathlib import Path

import pytest

from chatbot_contracts.enums import RegionKind, SourceType
from chatbot_contracts.knowledge_base import DocumentVersion, Region
from chatbot_platform import ingest
from chatbot_platform.documents import register_document
from chatbot_platform.errors import NotFoundError
from chatbot_platform.factory import Platform
from chatbot_platform.settings import RAW_BUCKET
from chatbot_platform.storage import split_uri
from chatbot_platform.testing import make_test_platform
from chatbot_w1_ingest import job

FIXTURES = Path(__file__).parent / "fixtures"
REGION_TABLE = "ingest.regions"
LAYOUT_PDF = (FIXTURES / "layout.pdf").read_bytes()


@pytest.fixture(scope="module")
def ran(tmp_path_factory) -> tuple[Platform, DocumentVersion, str, int]:
    """One ingestion run of the layout fixture, shared by the assertions below."""
    platform = make_test_platform(tmp_path_factory.mktemp("w1"))
    document = register_document(
        platform.registry,
        platform.store,
        LAYOUT_PDF,
        filename="layout.pdf",
        course_code="DANA4850",
        source_id="lecture notes 3",
        source_type=SourceType.LECTURE_NOTE,
    )
    run_id = platform.registry.start_run(document.doc_version)
    return platform, document, run_id, job.run(platform, run_id, document.doc_version)


@pytest.fixture
def regions(ran) -> list[Region]:
    platform, _document, _run_id, _written = ran
    return ingest.read_records(platform.engine, REGION_TABLE, Region)


def test_the_run_writes_one_row_per_region(ran, regions):
    _platform, document, run_id, written = ran
    assert written == len(regions)
    assert {region.ingestion_run_id for region in regions} == {run_id}
    assert {region.doc_version for region in regions} == {document.doc_version}


def test_the_run_sets_the_page_count(ran):
    platform, document, _run_id, _written = ran
    assert document.page_count is None
    assert platform.registry.get_doc_version(document.doc_version).page_count == 2


def test_every_page_of_the_document_has_a_region(regions):
    assert {region.page_no for region in regions} == {1, 2}
    assert len({region.region_id for region in regions}) == len(regions)


def test_the_table_region_kept_its_text(regions):
    tables = [region for region in regions if region.kind is RegionKind.TABLE]
    assert len(tables) == 1
    assert "2.5" in tables[0].raw_text


def test_figure_pictures_land_in_the_raw_bucket(ran, regions):
    platform, _document, _run_id, _written = ran
    figures = [region for region in regions if region.kind is RegionKind.FIGURE]
    assert figures
    keys = platform.store.list_keys(RAW_BUCKET)
    for region in figures:
        bucket, key = split_uri(region.image_uri)
        assert bucket == RAW_BUCKET
        assert key in keys
        assert platform.store.get(bucket, key).startswith(b"\x89PNG")


def test_the_raw_file_is_left_alone(ran):
    platform, document, _run_id, _written = ran
    bucket, key = split_uri(document.raw_uri)
    assert platform.store.get(bucket, key) == LAYOUT_PDF


def test_running_the_job_twice_keeps_one_row_per_region(ran, regions):
    platform, document, run_id, _written = ran
    assert job.run(platform, run_id, document.doc_version) == len(regions)
    assert len(ingest.read_records(platform.engine, REGION_TABLE, Region)) == len(regions)


def test_regions_of_another_run_are_not_returned(ran, regions):
    platform, document, _run_id, _written = ran
    other = platform.registry.start_run(document.doc_version)
    assert other not in {region.ingestion_run_id for region in regions}
    assert len(ingest.read_records(platform.engine, REGION_TABLE, Region, [other])) == 0


def test_an_unknown_document_version_stops_the_job(tmp_path):
    platform = make_test_platform(tmp_path)
    with pytest.raises(NotFoundError):
        job.run(platform, "run-abc123", "dana4850/nothing@000000000000")
    assert ingest.read_records(platform.engine, REGION_TABLE, Region) == []
