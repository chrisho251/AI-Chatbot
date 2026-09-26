"""Layout analysis with Docling. Stub owned by Lane B.

Purpose
Split every page of a PDF, slide deck or scan into typed regions. The kinds are text, figure,
scan, table, equation and code, see RegionKind. REGION_HANDLERS in the knowledge_base module
of chatbot_contracts says
which worker extracts each kind.

Input
The raw file bytes, the document version and the ingestion run id.

Output
A LayoutResult with the page count and every region in reading order. Region ids must be stable,
for example the document version, page number and position on the page joined together.

What to build
Convert with the Docling DocumentConverter and map each Docling item to a RegionKind.
Keep the bbox, keep raw_text for text, table and code regions.
Store images of figure and scan regions in the raw bucket under a derived key and set image_uri.
Every page must yield at least one region, blank pages yield one empty text region, otherwise the
quality gate page coverage check fails.

How to test
Keep a small PDF with text, a table, an equation and a code listing under tests/fixtures.
Assert the page count, one region per page at least, and the kinds you expect.
"""

from dataclasses import dataclass

from chatbot_contracts.knowledge_base import Region


@dataclass(frozen=True)
class LayoutResult:
    page_count: int
    regions: list[Region]


def analyze(data: bytes, doc_version: str, run_id: str) -> LayoutResult:
    raise NotImplementedError("layout analysis is not written yet")
