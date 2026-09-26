"""Compute the four RAGAs metrics. Stub owned by Lane D.

Purpose
Context precision, faithfulness, answer relevancy and context recall, Appendix A.6. Scores go to
eval.ragas_scores with the knowledge base, model, prompt and judge versions of the run. The mean per
metric also goes to reporting.ragas_summary, which the quality dashboard reads.

What to build
Send each golden item to the gateway ask endpoint with a test student token and read the contexts
of that request from ops.citations and the serving index, or read sampled live interactions for
the reference free metrics. Run RAGAs with the self hosted judge through its OpenAI compatible API
and the same embeddings as serving. The judge comes from another model family than the generator,
so it does not favour its own answers. Never call a paid API. Run off peak, the judge competes for
the GPU. Keep the item level scores of a run as a Parquet export too, with
chatbot_platform.exports.export_rows.

How to test
Two golden items with a faked judge give one row per item and metric.
"""

from chatbot_eval.golden_set import GoldenItem


def run(items: list[GoldenItem], kb_version: int, dataset: str) -> str:
    """Score the items and return the run id."""
    raise NotImplementedError("RAGAs runs are not written yet")
