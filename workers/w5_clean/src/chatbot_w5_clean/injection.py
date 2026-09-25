"""Scan text for hidden instructions aimed at the model. Stub owned by Lane B.

Purpose
Indirect prompt injection hides instructions inside sources or web pages. Offline, flagged regions
are quarantined and counted in PageFlags.injection_hits. Online, flagged uploads and web pages are
dropped. Every detection is also an obs.guard_events row with stage w5_ingest or w5_online,
and a GUARD_EVENTS count from chatbot_common.metrics.

What to build
The prompt injection classifier named in TECH_STACK.md, run per paragraph with transformers on CPU,
plus a few cheap patterns for phrases like ignore previous instructions.

How to test
A paragraph with an embedded instruction is flagged, a normal statistics paragraph is not.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class InjectionScan:
    hits: int
    flagged_paragraphs: list[int]


def scan(text: str) -> InjectionScan:
    raise NotImplementedError("injection scan is not written yet")
