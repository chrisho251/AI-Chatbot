"""Choose the embedding backend.

Purpose
Use TEI over HTTP where it runs, and an in process sentence transformers model on machines where it
does not, such as arm64 laptops. Both satisfy the Embedder protocol in chatbot_common.embeddings.

What to build
LocalEmbedder loads the model named in settings once and embeds in batches with normalization on.
build_embedder returns TeiEmbedder when CHATBOT_EMBED_BASE_URL answers and LocalEmbedder
otherwise, or follows an explicit setting if you add one.

How to test
LocalEmbedder with a tiny public model returns unit vectors of the right dimension.
"""

import os
from collections.abc import Sequence

from sentence_transformers import SentenceTransformer

from chatbot_common.embeddings import Embedder, TeiEmbedder
from chatbot_common.settings import ServiceSettings


class LocalEmbedder:
    def __init__(self, model: str) -> None:
        self.model = model
        self._model = SentenceTransformer(model)

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        embeddings = self._model.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embeddings.tolist()


def build_embedder(settings: ServiceSettings) -> Embedder:
    embed_base_url = os.environ.get("CHATBOT_EMBED_BASE_URL", settings.embed_base_url)
    if embed_base_url:
        return TeiEmbedder(base_url=embed_base_url, model=settings.llm_model)
    return LocalEmbedder(model=settings.llm_model)