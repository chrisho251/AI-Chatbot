"""Embed the student question at answer time. Stub owned by Lane B.

Purpose
Appendix A.4 gives query embedding to W6. The vector must come from the same model as the
knowledge base version it will search, otherwise retrieval returns nonsense.

Input
An EmbedRequest with the texts and the knowledge base version pinned by the orchestrator.

Output
An EmbedResult with one vector per text and the embedding model name.

What to build
Read the embedding model of the knowledge base version from the platform registry, refuse with
HTTP 409 when it differs from the loaded encoder, then embed with the encoder from
encoder.build_embedder.

How to test
With make_test_platform, publish a version encoded with another model name and assert the refusal.
"""

from chatbot_contracts.query import EmbedRequest, EmbedResult


async def embed_query(request: EmbedRequest) -> EmbedResult:
    raise NotImplementedError("query embedding is not written yet")
