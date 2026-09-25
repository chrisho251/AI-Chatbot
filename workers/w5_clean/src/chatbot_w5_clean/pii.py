"""PII scrubbing with Microsoft Presidio. Stub owned by Lane B.

Purpose
Past exam papers can contain student names and ids. Scrub them before anything is chunked, and
scrub student questions before they are logged for evaluation or fine tuning.

Output
ScrubResult with the scrubbed text, hits for entities found and replaced, and remaining for entities
still found by a second pass. The quality gate requires remaining to be zero on every page.

What to build
Presidio AnalyzerEngine with the spaCy English model and AnonymizerEngine replacing entities with
a placeholder per entity type. The spaCy model is installed separately, see the README.

How to test
A sentence with a name, an email and a student number comes back scrubbed with hits equal to 3.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScrubResult:
    text: str
    hits: int
    remaining: int


def scrub(text: str) -> ScrubResult:
    raise NotImplementedError("PII scrubbing is not written yet")
