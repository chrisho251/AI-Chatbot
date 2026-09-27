"""Layout analysis on a born digital PDF, a blank page and the kind mapping."""

from pathlib import Path

import pytest
from docling_core.types.doc.labels import DocItemLabel

from chatbot_contracts.enums import RegionKind
from chatbot_w1_ingest import layout

FIXTURES = Path(__file__).parent / "fixtures"
DOC_VERSION = "dana4850/notes@abc123def456"
RUN_ID = "run-abc123"


@pytest.fixture(scope="session")
def analyzed():
    return layout.analyze((FIXTURES / "layout.pdf").read_bytes(), DOC_VERSION, RUN_ID)


@pytest.fixture(scope="session")
def blank():
    return layout.analyze((FIXTURES / "blank.pdf").read_bytes(), DOC_VERSION, RUN_ID)


def test_page_count_matches_the_file(analyzed):
    assert analyzed.page_count == 2


def test_every_page_has_at_least_one_region(analyzed, blank):
    for result in (analyzed, blank):
        pages = [region.page_no for region in result.regions]
        assert set(pages) == set(range(1, result.page_count + 1))
        assert len(pages) == len(result.regions)


def test_a_blank_page_gets_one_empty_text_region(blank):
    first = [region for region in blank.regions if region.page_no == 1]
    assert len(first) == 1
    assert first[0].kind is RegionKind.TEXT
    assert first[0].raw_text == ""
    assert first[0].bbox is None


def test_regions_come_in_reading_order(analyzed):
    assert [region.page_no for region in analyzed.regions] == sorted(
        region.page_no for region in analyzed.regions
    )
    assert [region.region_id.rsplit("r", 1)[-1] for region in analyzed.regions[:2]] == [
        "000",
        "001",
    ]


def test_the_named_kinds_are_found(analyzed):
    kinds = {region.kind for region in analyzed.regions}
    assert {RegionKind.TEXT, RegionKind.TABLE, RegionKind.EQUATION, RegionKind.FIGURE} <= kinds


def test_a_table_keeps_its_text_and_its_cells_are_not_regions(analyzed):
    tables = [region for region in analyzed.regions if region.kind is RegionKind.TABLE]
    assert len(tables) == 1
    assert "2.5" in tables[0].raw_text
    assert tables[0].raw_text.count("|") > 4


def test_a_text_region_keeps_its_text_and_an_equation_does_not(analyzed):
    body = [region for region in analyzed.regions if region.raw_text]
    assert any("normal equations" in region.raw_text for region in body)
    equations = [region for region in analyzed.regions if region.kind is RegionKind.EQUATION]
    assert equations and all(region.raw_text is None for region in equations)


def test_a_figure_has_a_box_and_no_raw_text(analyzed):
    figures = [region for region in analyzed.regions if region.kind is RegionKind.FIGURE]
    assert figures
    for region in figures:
        left, top, right, bottom = region.bbox
        assert left < right and top < bottom
        assert region.raw_text is None


def test_boxes_stay_inside_the_page(analyzed):
    for region in analyzed.regions:
        left, top, right, bottom = region.bbox
        assert 0 <= left < right <= 612
        assert 0 <= top < bottom <= 792


def test_regions_carry_the_run_and_the_document(analyzed):
    for region in analyzed.regions:
        assert region.ingestion_run_id == RUN_ID
        assert region.doc_version == DOC_VERSION
        assert region.producer == layout.PRODUCER
        assert region.schema_version != ""


def test_no_picture_is_stored_without_a_store(analyzed):
    assert all(region.image_uri is None for region in analyzed.regions)


def test_region_ids_are_built_from_version_page_and_position():
    assert layout.make_region_id("dana4850/notes@abc123def456", 7, 2) == (
        "dana4850/notes@abc123def456#p0007r002"
    )


def test_picture_keys_are_derived_not_random():
    key = layout.image_key("dana4850/notes@abc123def456", "dana4850/notes@abc123def456#p0001r000")
    assert key == layout.image_key(
        "dana4850/notes@abc123def456", "dana4850/notes@abc123def456#p0001r000"
    )
    assert key.endswith(".png")
    assert ".." not in key


@pytest.mark.parametrize(
    ("label", "picture_class", "expected"),
    [
        (DocItemLabel.CODE, None, RegionKind.CODE),
        (DocItemLabel.FORMULA, None, RegionKind.EQUATION),
        (DocItemLabel.TABLE, None, RegionKind.TABLE),
        (DocItemLabel.PICTURE, "full_page_image", RegionKind.SCAN),
        (DocItemLabel.PICTURE, "line_chart", RegionKind.FIGURE),
        (DocItemLabel.PICTURE, None, RegionKind.FIGURE),
        (DocItemLabel.CHART, "bar_chart", RegionKind.FIGURE),
        (DocItemLabel.TEXT, None, RegionKind.TEXT),
        (DocItemLabel.SECTION_HEADER, None, RegionKind.TEXT),
        (DocItemLabel.PAGE_FOOTER, None, RegionKind.TEXT),
        (DocItemLabel.LIST_ITEM, None, RegionKind.TEXT),
    ],
)
def test_every_docling_label_maps_to_a_kind(label, picture_class, expected):
    assert layout.region_kind(label, picture_class) is expected


def test_every_kind_in_the_contract_is_reachable_from_a_docling_label():
    produced = {layout.region_kind(label) for label in DocItemLabel}
    produced |= {layout.region_kind(DocItemLabel.PICTURE, name) for name in layout.SCAN_CLASSES}
    assert produced == set(RegionKind)
