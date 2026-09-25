"""OCR for scanned pages and image tables. Stub owned by Lane B.

Purpose
Turn the image of a scan or table region into markdown text with a confidence score.
Tables that already have raw_text from layout analysis pass through as markdown without OCR.

Input
A Region and the image bytes loaded from its image_uri.

Output
An ExtractedRegion with content in markdown and confidence between 0 and 1. W5 copies the lowest
confidence of a page into PageFlags.min_ocr_conf and the quality gate blocks pages below the
threshold.

What to build
Use the Docling OCR pipeline, RapidOCR or EasyOCR through Docling. Record the engine name and
version in Extractor so lineage shows which OCR produced the text.

How to test
Render a line of known text to a PNG in the test, run ocr_region and compare the words.
"""

from chatbot_contracts.corpus import ExtractedRegion, Region


def ocr_region(region: Region, image: bytes) -> ExtractedRegion:
    raise NotImplementedError("OCR is not written yet")
