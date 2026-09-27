"""Layout analysis with Docling, splitting pages into typed regions.

Every page of a PDF, slide deck or scan becomes a list of Region records with a kind out of
RegionKind. REGION_HANDLERS in the knowledge_base module of chatbot_contracts says which worker
extracts each kind, so W1 only has to get the split right.

Region ids are stable, the document version, the page number and the position of the region on the
page joined together. Every page yields at least one region and a blank page yields one empty text
region, otherwise the page coverage check of the quality gate fails.

Figure and scan pictures are cut out of the rendered page and written to the raw bucket under a
derived key, so a repeated run over the same file stores the same objects. The raw text of text,
table and code regions is kept, the rest is left to the worker that owns the kind.

OCR belongs to W2 and the code and formula models to W3 and W4, so layout runs the layout, table
and picture classification models only. A picture is a scan when the classifier says it covers a
whole page, and a figure otherwise.
"""

import io
from collections import defaultdict
from dataclasses import dataclass

from docling.datamodel.base_models import DocumentStream, InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import DoclingDocument
from docling_core.types.doc.document import DocItem, PageItem, TableItem
from docling_core.types.doc.labels import DocItemLabel

from chatbot_contracts.enums import RegionKind
from chatbot_contracts.knowledge_base import Region
from chatbot_platform.settings import RAW_BUCKET
from chatbot_platform.storage import ObjectStore

PRODUCER = "w1_ingest"
"""Recorded on every region, so lineage can name the worker that wrote a row."""

IMAGE_SCALE = 2.0
"""Page images are rendered at twice the PDF size, which keeps small captions readable."""

IMAGE_FORMAT = "PNG"
"""Region pictures are lossless, so OCR and a caption model read them without artefacts."""

SOURCE_NAME = "source.pdf"
"""Docling picks its reader from the file name of a stream."""

KIND_BY_LABEL: dict[DocItemLabel, RegionKind] = {
    DocItemLabel.CODE: RegionKind.CODE,
    DocItemLabel.FORMULA: RegionKind.EQUATION,
    DocItemLabel.TABLE: RegionKind.TABLE,
}
"""The Docling labels that name a kind on their own."""

PICTURE_LABELS = frozenset({DocItemLabel.PICTURE, DocItemLabel.CHART})
"""The labels that carry a picture and may be a figure or a scan."""

SCAN_CLASSES = frozenset({"full_page_image"})
"""The picture classes of a scanned page, which W2 has to read with OCR."""

RAW_TEXT_KINDS = frozenset({RegionKind.TEXT, RegionKind.TABLE, RegionKind.CODE})
"""The kinds W5 and W3 read as text, so their raw text has to be kept."""

IMAGE_KINDS = frozenset({RegionKind.FIGURE, RegionKind.SCAN})
"""The kinds W2 needs a picture of, stored next to the raw file."""


@dataclass(frozen=True)
class LayoutResult:
    page_count: int
    regions: list[Region]


def make_region_id(doc_version: str, page_no: int, position: int) -> str:
    """Stable region id. The same file and the same reader always give the same id."""
    return f"{doc_version}#p{page_no:04d}r{position:03d}"


def image_key(doc_version: str, region_id: str) -> str:
    """Key of a region picture in the raw bucket. It is derived, never random."""
    return f"regions/{doc_version}/{region_id}.png"


def region_kind(label: DocItemLabel, picture_class: str | None = None) -> RegionKind:
    """The kind of one Docling item. A picture covering a whole page is a scan, not a figure."""
    kind = KIND_BY_LABEL.get(label)
    if kind is not None:
        return kind
    if label in PICTURE_LABELS:
        return RegionKind.SCAN if picture_class in SCAN_CLASSES else RegionKind.FIGURE
    return RegionKind.TEXT


def analyze(
    data: bytes,
    doc_version: str,
    run_id: str,
    store: ObjectStore | None = None,
) -> LayoutResult:
    """Read the file, split it into regions and return them in reading order."""
    document = _convert(data, want_images=store is not None)
    page_count = len(document.pages)
    by_page: dict[int, list[Region]] = defaultdict(list)
    inside_tables = {_ref(table.self_ref) for table in document.tables}
    for node, _level in document.iterate_items():
        if not isinstance(node, DocItem) or not node.prov:
            continue
        if _ref(node.parent) in inside_tables:
            continue
        page_no = node.prov[0].page_no
        position = len(by_page[page_no])
        by_page[page_no].append(
            _region(document, node, page_no, position, doc_version, run_id, store)
        )

    regions: list[Region] = []
    for page_no in range(1, page_count + 1):
        regions.extend(by_page.get(page_no) or [_blank(doc_version, run_id, page_no)])
    return LayoutResult(page_count=page_count, regions=regions)


def _convert(data: bytes, *, want_images: bool) -> DoclingDocument:
    options = PdfPipelineOptions()
    options.do_ocr = False
    options.do_table_structure = True
    options.do_picture_classification = True
    options.generate_page_images = want_images
    options.images_scale = IMAGE_SCALE
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )
    return converter.convert(DocumentStream(name=SOURCE_NAME, stream=io.BytesIO(data))).document


def _region(
    document: DoclingDocument,
    item: DocItem,
    page_no: int,
    position: int,
    doc_version: str,
    run_id: str,
    store: ObjectStore | None,
) -> Region:
    page = document.pages[page_no]
    bbox = _bbox(item, page)
    kind = region_kind(item.label, _picture_class(item))
    rid = make_region_id(doc_version, page_no, position)
    image_uri = None
    if store is not None and kind in IMAGE_KINDS and bbox is not None:
        image_uri = store.put(RAW_BUCKET, image_key(doc_version, rid), _crop(page, bbox))
    return Region(
        ingestion_run_id=run_id,
        producer=PRODUCER,
        region_id=rid,
        doc_version=doc_version,
        page_no=page_no,
        kind=kind,
        bbox=bbox,
        raw_text=_raw_text(document, item) if kind in RAW_TEXT_KINDS else None,
        image_uri=image_uri,
    )


def _blank(doc_version: str, run_id: str, page_no: int) -> Region:
    """A blank page still gets one region, otherwise page coverage fails in the quality gate."""
    return Region(
        ingestion_run_id=run_id,
        producer=PRODUCER,
        region_id=make_region_id(doc_version, page_no, 0),
        doc_version=doc_version,
        page_no=page_no,
        kind=RegionKind.TEXT,
        raw_text="",
    )


def _bbox(item: DocItem, page: PageItem) -> tuple[float, float, float, float] | None:
    """Left, top, right and bottom in PDF points, measured from the top left of the page."""
    if not item.prov:
        return None
    box = item.prov[0].bbox.to_top_left_origin(page.size.height)
    return (box.l, box.t, box.r, box.b)


def _crop(page: PageItem, bbox: tuple[float, float, float, float]) -> bytes:
    """The part of the rendered page that the region covers, as an image in memory."""
    image = page.image.pil_image if page.image else None
    if image is None:
        raise ValueError(f"page {page.page_no} has no rendered image to cut a region out of")
    width, height = page.size.width, page.size.height
    left, top, right, bottom = bbox
    box = (
        round(left / width * image.width),
        round(top / height * image.height),
        round(right / width * image.width),
        round(bottom / height * image.height),
    )
    buffer = io.BytesIO()
    image.crop(box).save(buffer, format=IMAGE_FORMAT)
    return buffer.getvalue()


def _raw_text(document: DoclingDocument, item: DocItem) -> str | None:
    if isinstance(item, TableItem):
        return item.export_to_markdown(document)
    return getattr(item, "text", None) or None


def _ref(node: object) -> str:
    """The tree path of a Docling node. The parent of an item is a reference, not the node."""
    return getattr(node, "cref", str(node))


def _picture_class(item: DocItem) -> str | None:
    """The picture class the classifier is most sure about, or None when it did not run."""
    classification = getattr(getattr(item, "meta", None), "classification", None)
    if classification is None:
        return None
    best = max(classification.predictions, key=lambda guess: guess.confidence, default=None)
    return best.class_name if best is not None else None
