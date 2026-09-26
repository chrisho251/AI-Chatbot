"""Internal hybrid retrieval on the pinned knowledge base version. Stub owned by Lane C.

Purpose
Always the first stage. Search the vetted knowledge base before anything external.

What to build
Dense search with the query vector and lexical search with the question on the platform
ServingIndex, both at request.kb_version. Fuse the two rankings with fusion.reciprocal_rank,
rerank the best 30 with the Reranker from chatbot_common.embeddings and keep request.k.
sufficiency is the top rerank score adjusted by its margin over the second one, clipped to 0 and 1.
Refuse when the knowledge base version uses another embedding model than the query vector came
from.
Report timings for dense, lexical and rerank in milliseconds.

How to test
Publish sample chunk sets into make_test_platform and query its InMemoryServingIndex, with a fake
reranker that returns fixed scores.
"""

from chatbot_contracts.query import RetrievalRequest, RetrievalResult


async def retrieve(request: RetrievalRequest) -> RetrievalResult:
    raise NotImplementedError("internal retrieval is not written yet")
