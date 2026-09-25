"""Confidence score and level. Stub owned by Lane C.

Purpose
One score from 0 to 1 decides between answering, answering with a caveat and escalating.

What to build
score combines four signals with hand set weights first, top rerank score and margin, NLI
groundedness per sentence, citation coverage and the guard verdict. Later the weights come from a
logistic regression fitted on SME labelled answers, keep the weights in one place for that.
level maps the score with the thresholds in OrchestratorSettings. L1 at or above l1_threshold,
L2 at or above l2_threshold, L3 below.

How to test
Table driven tests on level at the exact thresholds, and a monotonic check on score.
"""

from dataclasses import dataclass

from chatbot_contracts.enums import ConfidenceLevel


@dataclass(frozen=True)
class Signals:
    rerank_top: float
    rerank_margin: float
    groundedness: float
    citation_coverage: float
    guard_ok: bool


def score(signals: Signals) -> float:
    raise NotImplementedError("confidence scoring is not written yet")


def level(value: float, l1_threshold: float, l2_threshold: float) -> ConfidenceLevel:
    raise NotImplementedError("confidence levels are not written yet")
