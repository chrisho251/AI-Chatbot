"""Embedding and rerank ports with clients for Text Embeddings Inference.

TEI runs on amd64 machines and on the GPU host. On arm64 laptops W6 and W7 can plug in an in process
adapter built on sentence transformers that satisfies the same protocol. That adapter belongs to the
worker that needs it, so heavy libraries stay out of this package.
"""

from collections.abc import Sequence
from typing import Protocol

import httpx


class Embedder(Protocol):
    model: str

    async def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class Reranker(Protocol):
    async def rerank(self, query: str, texts: Sequence[str]) -> list[float]:
        """One relevance score per text, in the input order."""
        ...


class TeiEmbedder:
    def __init__(self, base_url: str, model: str, client: httpx.AsyncClient | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = client or httpx.AsyncClient(timeout=30.0)

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        response = await self._client.post(
            f"{self.base_url}/embed", json={"inputs": list(texts), "normalize": True}
        )
        response.raise_for_status()
        return response.json()


class TeiReranker:
    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=30.0)

    async def rerank(self, query: str, texts: Sequence[str]) -> list[float]:
        response = await self._client.post(
            f"{self.base_url}/rerank", json={"query": query, "texts": list(texts)}
        )
        response.raise_for_status()
        scores = [0.0] * len(texts)
        for item in response.json():
            scores[item["index"]] = item["score"]
        return scores
