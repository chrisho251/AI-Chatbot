"""Client for the self hosted LLM. llama.cpp and vLLM both expose the OpenAI chat API.

W8 uses it for answers, W3 for code generation and W2 for photos through a vision model.
"""

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx

from chatbot_common.settings import ServiceSettings

Message = dict[str, Any]


@dataclass(frozen=True)
class Completion:
    text: str
    tokens_in: int
    tokens_out: int


class ChatClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        client: httpx.AsyncClient | None = None,
        timeout_s: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = client or httpx.AsyncClient(timeout=timeout_s)

    @classmethod
    def from_settings(cls, settings: ServiceSettings) -> "ChatClient":
        return cls(settings.llm_base_url, settings.llm_model, timeout_s=settings.request_timeout_s)

    async def complete(self, messages: list[Message], **params: Any) -> Completion:
        body = {"model": self.model, "messages": messages, **params}
        response = await self._client.post(f"{self.base_url}/chat/completions", json=body)
        response.raise_for_status()
        data = response.json()
        usage = data.get("usage") or {}
        return Completion(
            text=data["choices"][0]["message"]["content"] or "",
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
        )

    async def stream(self, messages: list[Message], **params: Any) -> AsyncIterator[str]:
        """Yield text pieces as the model produces them."""
        body = {"model": self.model, "messages": messages, "stream": True, **params}
        url = f"{self.base_url}/chat/completions"
        async with self._client.stream("POST", url, json=body) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                payload = line.removeprefix("data: ").strip()
                if not line.startswith("data: ") or payload == "[DONE]":
                    continue
                delta = json.loads(payload)["choices"][0].get("delta", {}).get("content")
                if delta:
                    yield delta

    async def aclose(self) -> None:
        await self._client.aclose()
