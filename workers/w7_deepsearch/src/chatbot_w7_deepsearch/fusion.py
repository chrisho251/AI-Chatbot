"""Rank fusion for hybrid search. Stub owned by Lane C.

What to build
Reciprocal rank fusion. Each ranking is a list of chunk ids, best first. A chunk scores the sum of
one over k plus its rank in every ranking where it appears, with k equal to 60 by default.
Return chunk ids ordered by fused score, ties broken by the order of the first ranking.

How to test
A chunk ranked first in both lists wins, a chunk found by only one list still appears.
"""


def reciprocal_rank(rankings: list[list[str]], k: int = 60) -> list[str]:
    raise NotImplementedError("rank fusion is not written yet")
