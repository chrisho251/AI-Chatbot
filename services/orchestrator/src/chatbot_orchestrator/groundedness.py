"""NLI groundedness per answer sentence. Stub owned by Lane C.

Purpose
Check each answer sentence against the chunk it cites. The share of entailed sentences is one of
the confidence signals.

What to build
A DeBERTa v3 MNLI class cross encoder loaded once with sentence transformers on CPU, see
TECH_STACK.md. Premise is the cited chunk text, hypothesis is the sentence. The pipeline calls it
with asyncio.to_thread, because it runs inside the api process.

How to test
An answer copied from its chunk scores near 1, a contradicting sentence scores near 0.
"""


def groundedness(sentences: list[str], cited_texts: list[str]) -> float:
    raise NotImplementedError("groundedness is not written yet")
