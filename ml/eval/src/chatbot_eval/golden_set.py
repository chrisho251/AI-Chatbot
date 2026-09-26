"""The golden set of questions with reference answers. Stub owned by Lane D.

Purpose
Context recall needs reference answers, so the four RAGAs metrics run on this set at every
candidate knowledge base version, at every model promotion and nightly. The same items drive
Appendix C testing, level 1 remembering and understanding, level 2 applying and analyzing across
sources, level 3 questions the knowledge base cannot answer.

What to build
GoldenItem, load from a reviewed JSONL file kept in the repo under ml/eval/data, and save to the
eval.test_cases table of chatbot_platform.sql. SMEs review every item.

How to test
Round trip a small JSONL file through load and save with make_test_platform.
"""

from pathlib import Path

from chatbot_contracts.base import Model


class GoldenItem(Model):
    item_id: str
    level: int
    question: str
    reference_answer: str
    reference_chunk_ids: list[str] = []
    course_code: str | None = None
    topic: str | None = None


def load(path: Path) -> list[GoldenItem]:
    raise NotImplementedError("golden set loading is not written yet")
