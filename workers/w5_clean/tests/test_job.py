"""Tests for the offline cleaning job."""

from chatbot_contracts import samples
from chatbot_contracts.knowledge_base import PageFlags
from chatbot_platform import ingest
from chatbot_w5_clean import job


def test_job_writes_one_clean_page_per_page(populated_platform):
    platform, run_id, doc = populated_platform
    count = job.run(platform, run_id, doc.doc_version)
    assert count == 3

    pages = ingest.read_clean_pages(platform.engine, [run_id])
    pages = [p for p in pages if p.doc_version == doc.doc_version]
    assert len(pages) == 3
    page_nos = sorted(p.page_no for p in pages)
    assert page_nos == [1, 2, 3]


def test_job_normalizes_text(populated_platform):
    platform, run_id, doc = populated_platform
    job.run(platform, run_id, doc.doc_version)
    pages = ingest.read_clean_pages(platform.engine, [run_id])
    pages = [p for p in pages if p.doc_version == doc.doc_version]
    page_one = next(p for p in pages if p.page_no == 1)
    assert samples.PAGE_TEXTS[0] in page_one.markdown


def test_job_scrubs_pii(populated_platform):
    platform, run_id, doc = populated_platform

    pii_region = samples.sample_region(
        ingestion_run_id=run_id,
        region_id="region-pii",
        page_no=2,
        raw_text="John Smith student 301001234 can be reached at js@example.com.",
        bbox=(0.0, 2.0, 100.0, 30.0),
    )
    ingest.append_records(platform.engine, "ingest.regions", [pii_region])

    count = job.run(platform, run_id, doc.doc_version)
    assert count == 3

    pages = ingest.read_clean_pages(platform.engine, [run_id])
    pages = [p for p in pages if p.doc_version == doc.doc_version]
    page_two = next(p for p in pages if p.page_no == 2)
    assert "John Smith" not in page_two.markdown
    assert "[NAME]" in page_two.markdown
    assert page_two.flags.pii_hits >= 1
    assert page_two.flags.pii_remaining == 0


def test_job_records_flags(populated_platform):
    platform, run_id, doc = populated_platform
    job.run(platform, run_id, doc.doc_version)
    pages = ingest.read_clean_pages(platform.engine, [run_id])
    pages = [p for p in pages if p.doc_version == doc.doc_version]
    for page in pages:
        assert isinstance(page.flags, PageFlags)
        assert page.flags.injection_hits == 0
        assert page.flags.dup_of is None


def test_job_handles_blank_pages(platform, make_run):
    """A blank page that W1 declared but has no regions still gets a CleanPage."""
    run_id, doc = make_run(platform, page_count=4, course_code="STAT 404")

    text_regions = [
        samples.sample_region(
            ingestion_run_id=run_id,
            region_id=f"region-blank-{i:04d}",
            page_no=i,
            raw_text=samples.PAGE_TEXTS[i - 1],
            bbox=(0.0, float(i), 100.0, 20.0),
        )
        for i in range(1, 4)
    ]
    ingest.append_records(platform.engine, "ingest.regions", text_regions)

    count = job.run(platform, run_id, doc.doc_version)
    assert count == 4

    pages = ingest.read_clean_pages(platform.engine, [run_id])
    pages = [p for p in pages if p.doc_version == doc.doc_version]
    page_nos = sorted(p.page_no for p in pages)
    assert page_nos == [1, 2, 3, 4]
    page_4 = next(p for p in pages if p.page_no == 4)
    assert page_4.markdown.strip() == ""
    assert page_4.region_ids == []


def test_job_joins_extracted_regions(populated_platform):
    platform, run_id, doc = populated_platform
    job.run(platform, run_id, doc.doc_version)

    pages = ingest.read_clean_pages(platform.engine, [run_id])
    pages = [p for p in pages if p.doc_version == doc.doc_version]
    page_one = next(p for p in pages if p.page_no == 1)
    assert "region-0099" in page_one.region_ids
    assert "\\bar{x}" in page_one.markdown


def test_job_returns_page_count(populated_platform):
    platform, run_id, doc = populated_platform
    count = job.run(platform, run_id, doc.doc_version)
    assert count == doc.page_count


def test_job_detects_duplicates(platform, make_run):
    """Two pages with identical text are flagged as duplicates."""
    run_id, doc = make_run(platform, page_count=2, course_code="STAT 303")

    text = "The mean is the sum of values divided by the number of values."
    regions = [
        samples.sample_region(
            ingestion_run_id=run_id,
            region_id=f"region-dup-{i:04d}",
            page_no=i,
            raw_text=text,
            bbox=(0.0, float(i), 100.0, 20.0),
        )
        for i in range(1, 3)
    ]
    ingest.append_records(platform.engine, "ingest.regions", regions)

    job.run(platform, run_id, doc.doc_version)

    pages = ingest.read_clean_pages(platform.engine, [run_id])
    pages = [p for p in pages if p.doc_version == doc.doc_version]
    page_two = next(p for p in pages if p.page_no == 2)
    assert page_two.flags.dup_of is not None
    page_one = next(p for p in pages if p.page_no == 1)
    assert page_one.flags.dup_of is None
