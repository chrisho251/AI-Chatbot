"""Build a fine tuning dataset. Stub owned by Lane D.

Purpose
Appendix A.5 asks for a documented dataset creation method from course materials. Sources are
SME written question and answer pairs and synthetic pairs generated from a knowledge base version
and reviewed by SMEs. Student interactions only if conflict 4 in ARCHITECTURE.md allows it.

What to build
Collect items, dedupe, scan for PII with the W5 rules, drop any item that overlaps the golden or
test sets and assign splits with split.assign. Then freeze the result. Write the items once as
Parquet with chatbot_platform.exports.export_rows, and store ft.items rows plus an ft.datasets row
with the export uri and the manifest hash of the items, which is the dataset version.

How to test
A duplicate and a golden set question are both removed, and building twice gives the same version.
"""


def build(kb_version: int, sources: list[str]) -> str:
    """Build and freeze a dataset, return its dataset version."""
    raise NotImplementedError("dataset building is not written yet")
