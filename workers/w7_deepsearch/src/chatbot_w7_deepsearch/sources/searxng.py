"""SearXNG source for W7 external search. Stub owned by Lane C.

Purpose
General web search through the self hosted SearXNG container, restricted to the
allowlist with site filters. This is how OpenStax and LibreTexts exercises are found.

What to build
An async search function over httpx that returns ExternalItem records with the licence filled in.
Respect the rate limit below, retry once on timeouts, and return an empty list when the source is
down so escalation can move on to the expert.

Rate limit
None of its own, the upstream engines may throttle.

How to test
Save one real response under tests/fixtures and serve it with an httpx MockTransport.
"""

from chatbot_contracts.external import ExternalItem


async def search(query: str, max_results: int) -> list[ExternalItem]:
    raise NotImplementedError("SearXNG search is not written yet")
