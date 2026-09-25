"""PubMed source for W7 external search. Stub owned by Lane C.

Purpose
Biomedical literature through the NCBI E utilities esearch and esummary calls.

What to build
An async search function over httpx that returns ExternalItem records with the licence filled in.
Respect the rate limit below, retry once on timeouts, and return an empty list when the source is
down so escalation can move on to the expert.

Rate limit
3 requests per second without an API key, 10 with a free key.

How to test
Save one real response under tests/fixtures and serve it with an httpx MockTransport.
"""

from chatbot_contracts.external import ExternalItem


async def search(query: str, max_results: int) -> list[ExternalItem]:
    raise NotImplementedError("PubMed search is not written yet")
