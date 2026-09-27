"""Scan text for hidden instructions aimed at the model.

Purpose
Indirect prompt injection hides instructions inside sources or web pages. Offline, flagged regions
are quarantined and counted in PageFlags.injection_hits. Online, flagged uploads and web pages are
dropped. Every detection is also an ops.guard_events row with stage w5_ingest or w5_online,
and a GUARD_EVENTS count from chatbot_common.metrics.

What to build
The prompt injection classifier named in TECH_STACK.md, run per paragraph with transformers on CPU,
plus a few cheap patterns for phrases like ignore previous instructions. Online it runs inside the
api process, so call it with asyncio.to_thread.

How to test
A paragraph with an embedded instruction is flagged, a normal statistics paragraph is not.
"""

import re
from dataclasses import dataclass
from functools import lru_cache

_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(
        r"disregard\s+(?:all\s+)?previous\s+(?:instructions|responses|output)", re.IGNORECASE
    ),
    re.compile(r"forget\s+(?:all\s+)?(your\s+)?(instructions|previous\s+response)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+chatgpt", re.IGNORECASE),
    re.compile(
        r"you\s+are\s+a\s+(?:chatbot|ai|assistant)\s+(?:with|and).{0,40}(no\s+restrictions|unlimited|unfiltered)",
        re.IGNORECASE,
    ),
    re.compile(r"new\s+instructions", re.IGNORECASE),
    re.compile(
        r"override\s+(?:the\s+)?(?:system\s+|your\s+)(?:instructions|rules|policies)", re.IGNORECASE
    ),
    re.compile(
        r"(?:act|pretend|play)\s+as\s+(?:if\s+)?(?:you\s+are\s+)?(an?\s+)?(?:un)?restricted",
        re.IGNORECASE,
    ),
    re.compile(r"system\s+(?:prompt|message|instructions?)\s*[:=]", re.IGNORECASE),
    re.compile(r"disregard\s+the\s+above", re.IGNORECASE),
    re.compile(
        r"(?:reveal|show|expose|provide)\s+(?:the\s+)?(?:full\s+)?(?:system|hidden).{0,30}(prompt|instructions|rules)",
        re.IGNORECASE,
    ),
    re.compile(r"bypass\s+(?:your\s+)?(?:safety|content|guidance)", re.IGNORECASE),
    re.compile(r"you\s+must\s+not\s+(refuse|reject|decline|warn)", re.IGNORECASE),
    re.compile(r"ignore\s+(?:the\s+)?(?:content|safety|guidance|filter)", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"dan\s+mode", re.IGNORECASE),
    re.compile(r"as\s+an\s+ai\s+assistant.{0,40}(you\s+should|should\s+not)", re.IGNORECASE),
]

_INJECTION_LABEL = "INJECTION"
_INJECTION_SCORE = 0.95

_MODEL_NAME = "ProtectAI/deberta-v3-base-prompt-injection-v2"


@dataclass(frozen=True)
class InjectionScan:
    hits: int
    flagged_paragraphs: list[int]


def _cheap_scan(text: str) -> set[int]:
    """Return indices of paragraphs flagged by cheap regex patterns."""
    paragraphs = text.split("\n\n")
    flagged: set[int] = set()
    for i, paragraph in enumerate(paragraphs):
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(paragraph):
                flagged.add(i)
                break
    return flagged


@lru_cache(maxsize=1)
def _load_classifier():
    """Lazy load the transformers classifier, returns None if unavailable."""
    try:
        import torch  # noqa: F401
    except ImportError:
        return None
    try:
        from transformers import pipeline

        return pipeline("text-classification", model=_MODEL_NAME)
    except Exception:
        return None


def _model_scan(text: str) -> set[int]:
    """Return indices of paragraphs flagged by the model classifier."""
    paragraphs = text.split("\n\n")
    classifier = _load_classifier()
    if classifier is None:
        return set()
    flagged: set[int] = set()
    for i, paragraph in enumerate(paragraphs):
        if not paragraph.strip():
            continue
        try:
            result = classifier(paragraph)
            if result and _is_injection_label(result[0]["label"]):
                flagged.add(i)
        except Exception:
            continue
    return flagged


def _is_injection_label(label: str) -> bool:
    normalized = label.strip().upper()
    return _INJECTION_LABEL in normalized or normalized == "INJECTED"


def scan(text: str) -> InjectionScan:
    """Scan text for prompt injection, returning hit count and flagged paragraph indices."""
    flagged = _cheap_scan(text)
    flagged.update(_model_scan(text))
    return InjectionScan(hits=len(flagged), flagged_paragraphs=sorted(flagged))
