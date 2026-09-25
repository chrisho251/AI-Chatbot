"""Generate the cited answer. Stub owned by Lane C.

Purpose
Synthesize retrieved context and computed results into the final answer, Appendix A.4.

What to build
Build messages with prompt.build_messages, stream from the LLM with ChatClient.stream, run tool
calls through tools.run when the model asks for a calculation or code, and parse citations with
citations.parse. generate_stream yields answer delta events and one answer final event carrying the
citations. generate returns the whole GenerationResult for batch callers such as the eval lane.
Count generated tokens in OUTPUT_TOKENS from chatbot_common.metrics.

How to test
Fake the LLM with an httpx MockTransport that streams a fixed answer with markers like [1], and fake
W3 and W4 with chatbot_common.testing.fake_client.
"""

from collections.abc import AsyncIterator

from chatbot_contracts.escalation import StreamEvent
from chatbot_contracts.query import GenerationRequest, GenerationResult


async def generate(request: GenerationRequest) -> GenerationResult:
    raise NotImplementedError("generation is not written yet")


def generate_stream(request: GenerationRequest) -> AsyncIterator[StreamEvent]:
    """Yield answer events. Write it as an async generator when implementing."""
    raise NotImplementedError("streamed generation is not written yet")
