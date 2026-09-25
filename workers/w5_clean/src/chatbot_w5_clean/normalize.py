"""Text normalization and boilerplate removal. Stub owned by Lane B.

Purpose
Fix encoding damage, unify whitespace and quotes, and remove running headers, footers and page
numbers that repeat on most pages of a document.

What to build
normalize fixes one text with ftfy and whitespace rules.
strip_boilerplate receives the pages of one document and drops lines that repeat on more than half
of the pages. Keep equations, code fences and tables untouched.

How to test
Three pages that share a header and a footer come back without them and nothing else changes.
"""


def normalize(text: str) -> str:
    raise NotImplementedError("normalize is not written yet")


def strip_boilerplate(pages: list[str]) -> list[str]:
    raise NotImplementedError("boilerplate removal is not written yet")
