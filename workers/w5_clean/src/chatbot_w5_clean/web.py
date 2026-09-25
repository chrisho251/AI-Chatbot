"""Extract readable text from a fetched web page. Stub owned by Lane B.

Purpose
W7 fetches pages from allowlisted external sources and sends their HTML here with origin external.

What to build
trafilatura extraction that keeps headings, lists and tables, and drops navigation and ads.
Return an empty string when nothing readable is left, the caller then skips the page.

How to test
Keep one saved HTML page under tests/fixtures and assert the exercise text survives.
"""


def extract_text(html: str) -> str:
    raise NotImplementedError("web page extraction is not written yet")
