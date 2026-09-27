"""Extract readable text from a fetched web page.

Purpose
W7 fetches pages from allowlisted external sources and sends their HTML here with origin external.

What to build
trafilatura extraction that keeps headings, lists and tables, and drops navigation and ads.
Return an empty string when nothing readable is left, the caller then skips the page.

How to test
Keep one saved HTML page under tests/fixtures and assert the exercise text survives.
"""

import trafilatura


def extract_text(html: str) -> str:
    """Extract readable text from HTML, dropping navigation and ads."""
    if not html or not html.strip():
        return ""
    extracted = trafilatura.extract(
        html,
        output_format="txt",
        include_comments=False,
        include_tables=True,
        include_images=False,
        favor_precision=True,
        fast=True,
    )
    return extracted or ""
