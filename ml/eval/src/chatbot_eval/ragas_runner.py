"""Compute the four RAGAs metrics. Stub owned by Lane D.

Purpose
Context precision, faithfulness, answer relevancy and context recall, Appendix A.6. Scores go to
eval.ragas_scores with the corpus, model, prompt and judge versions of the run. The mean per
metric also goes to reporting.ragas_summary, which the quality dashboard reads.

What to build
Ask the orchestrator for each golden item, or read sampled live interactions for the reference free
metrics. Run RAGAs with the self hosted judge model through its OpenAI compatible API and the same
embeddings as serving. Never call a paid API. Run off peak, the judge competes for the GPU.

How to test
Two golden items with a faked judge give one row per item and metric.
"""

from chatbot_eval.golden_set import GoldenItem


def run(items: list[GoldenItem], corpus_version: int, dataset: str) -> str:
    """Score the items and return the run id."""
    raise NotImplementedError("RAGAs runs are not written yet")
