"""Choose the embedding backend. Stub owned by Lane B.

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

from collections.abc import Sequence

from chatbot_common.embeddings import Embedder
from chatbot_common.settings import ServiceSettings


class LocalEmbedder:
    def __init__(self, model: str) -> None:
        self.model = model

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        raise NotImplementedError("in process embeddings are not written yet")


def build_embedder(settings: ServiceSettings) -> Embedder:
    raise NotImplementedError("embedder selection is not written yet")
