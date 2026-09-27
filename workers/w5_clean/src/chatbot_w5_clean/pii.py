"""PII scrubbing with Microsoft Presidio.

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

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

PII_ENTITIES = ["PERSON", "EMAIL_ADDRESS", "STUDENT_NUMBER"]

_PLACEHOLDERS = {
    "PERSON": "[NAME]",
    "EMAIL_ADDRESS": "[EMAIL]",
    "STUDENT_NUMBER": "[STUDENT_ID]",
}


@dataclass(frozen=True)
class ScrubResult:
    text: str
    hits: int
    remaining: int


_student_number = PatternRecognizer(
    supported_entity="STUDENT_NUMBER",
    patterns=[Pattern("student number", r"\b\d{7,10}\b", 0.5)],
)


def _operators():
    return {
        entity: OperatorConfig("replace", {"new_value": placeholder})
        for entity, placeholder in _PLACEHOLDERS.items()
    }


_analyzer: AnalyzerEngine | None = None
_anonymizer: AnonymizerEngine | None = None


def _get_analyzer() -> AnalyzerEngine:
    global _analyzer
    if _analyzer is None:
        _analyzer = AnalyzerEngine()
        _analyzer.registry.add_recognizer(_student_number)
    return _analyzer


def _get_anonymizer() -> AnonymizerEngine:
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = AnonymizerEngine()
    return _anonymizer


def scrub(text: str) -> ScrubResult:
    """Scrub PII from text, returning the scrubbed text plus hit counts."""
    analyzer = _get_analyzer()
    anonymizer = _get_anonymizer()
    results = analyzer.analyze(text=text, language="en", entities=PII_ENTITIES)
    ops = {
        entity: op
        for entity, op in _operators().items()
        if entity in {r.entity_type for r in results}
    }
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results, operators=ops)
    scrubbed = anonymized.text
    remaining_results = analyzer.analyze(text=scrubbed, language="en", entities=PII_ENTITIES)
    return ScrubResult(text=scrubbed, hits=len(results), remaining=len(remaining_results))
