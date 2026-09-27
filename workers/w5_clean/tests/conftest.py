"""Test fixtures for W5 clean."""

from pathlib import Path

import pytest

from chatbot_contracts import samples
from chatbot_contracts.enums import RegionKind
from chatbot_platform import ingest
from chatbot_platform.testing import make_test_platform


@pytest.fixture
def platform(tmp_path: Path):
    return make_test_platform(tmp_path)


@pytest.fixture
def registered_run(platform):
    """A document version and an ingestion run ready for regions."""
    doc = samples.sample_document_version()
    platform.registry.add_doc_version(doc)
    run_id = platform.registry.start_run(doc.doc_version)
    return run_id, doc


@pytest.fixture
def populated_platform(platform, registered_run):
    """A platform with sample text regions for three pages plus an equation region."""
    run_id, doc = registered_run

    text_regions = [
        samples.sample_region(
            ingestion_run_id=run_id,
            region_id=f"region-{i:04d}",
            page_no=i,
            raw_text=samples.PAGE_TEXTS[i - 1],
            bbox=(0.0, float(i), 100.0, 20.0),
        )
        for i in range(1, 4)
    ]

    equation_region = samples.sample_region(
        ingestion_run_id=run_id,
        region_id="region-0099",
        page_no=1,
        kind=RegionKind.EQUATION,
        bbox=(0.0, 0.1, 100.0, 5.0),
        image_uri="s3://raw/6e/eq-0099.png",
    )
    equation_extracted = samples.sample_extracted_region(
        ingestion_run_id=run_id,
        region_id="region-0099",
        kind=RegionKind.EQUATION,
        content=r"\bar{x} = \frac{1}{n}\sum x_i",
        confidence=0.95,
    )

    ingest.append_records(platform.engine, "ingest.regions", text_regions + [equation_region])
    ingest.append_records(platform.engine, "ingest.extracted_regions", [equation_extracted])

    return platform, run_id, doc


@pytest.fixture
def make_run():
    """Factory to register a fresh document version and start a run for it."""

    def _make(platform, page_count: int, course_code: str = "STAT 202"):
        sha = samples.sha256_hex(course_code.encode())
        doc_id = samples.make_doc_id(course_code, course_code.lower())
        doc_version = samples.make_doc_version(doc_id, sha)
        doc = samples.sample_document_version(
            doc_id=doc_id,
            doc_version=doc_version,
            sha256=sha,
            course_code=course_code,
            source_id=course_code.lower(),
            page_count=page_count,
        )
        platform.registry.add_doc_version(doc)
        run_id = platform.registry.start_run(doc.doc_version)
        return run_id, doc

    return _make
