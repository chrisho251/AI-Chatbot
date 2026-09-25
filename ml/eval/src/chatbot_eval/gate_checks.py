"""Retrieval and RAGAs checks for the platform quality gate. Stub owned by Lane D.

Purpose
The gate in chatbot_platform.gate reports these two checks as skipped until this module provides
them. The pipeline passes them to run_gate next to default_checks.

What to build
retrieval_regression compares recall at k and MRR of the candidate with the serving version on the
golden set, within a tolerance. ragas_regression does the same for context precision and context
recall. Each returns a Check, a function from GateContext to CheckResult with the same name as the
placeholder it replaces.

How to test
Fake the retrieval of both versions and assert pass and fail around the tolerance.
"""

from chatbot_platform.gate import Check


def retrieval_regression(tolerance: float = 0.02) -> Check:
    raise NotImplementedError("the retrieval regression check is not written yet")


def ragas_regression(tolerance: float = 0.02) -> Check:
    raise NotImplementedError("the RAGAs regression check is not written yet")
