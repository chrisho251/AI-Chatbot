"""Build a fine tuning dataset. Stub owned by Lane D.

Purpose
Appendix A.5 asks for a documented dataset creation method from Health Science course materials.
Sources are SME written question and answer pairs and synthetic pairs generated from a corpus
version and reviewed by SMEs. Student interactions only if conflict 4 in ARCHITECTURE.md allows it.

What to build
Collect items, dedupe, scan for PII with the W5 rules, drop any item that overlaps the golden or
test sets, assign splits with split.assign, then freeze the result as ft.items rows plus an
ft.datasets row whose manifest hash is the dataset version.

How to test
A duplicate and a golden set question are both removed, and building twice gives the same version.
"""


def build(corpus_version: int, sources: list[str]) -> str:
    """Build and freeze a dataset, return its dataset version."""
    raise NotImplementedError("dataset building is not written yet")
