"""Embed the student question at answer time.

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

from fastapi import HTTPException

from chatbot_contracts.query import EmbedRequest, EmbedResult
from chatbot_platform.factory import build_platform
from chatbot_w6_embed.encoder import build_embedder


async def embed_query(request: EmbedRequest) -> EmbedResult:
    platform = build_platform()
    kb_version = platform.registry.get_kb_version(request.kb_version)
    kb_model = kb_version.embedding_model

    settings = platform.settings
    loaded_model = settings.llm_model

    if kb_model != loaded_model:
        raise HTTPException(
            status_code=409,
            detail=(
                f"KB version {request.kb_version} uses embedding model "
                f"'{kb_model}' but this worker loads '{loaded_model}'"
            ),
        )

    embedder = build_embedder(settings)
    vectors = embedder.embed(request.texts)

    return EmbedResult(vectors=vectors, embedding_model=kb_model)