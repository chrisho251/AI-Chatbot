"""MedlinePlus source for W7 external search. Stub owned by Lane C.

Purpose
Consumer health topics through the MedlinePlus web service.

What to build
An async search function over httpx that returns ExternalItem records with the licence filled in.
Respect the rate limit below, retry once on timeouts, and return an empty list when the source is
down so escalation can move on to the expert.

Rate limit
Fair use, keep it under a few requests per second.

How to test
Save one real response under tests/fixtures and serve it with an httpx MockTransport.
"""

from chatbot_contracts.external import ExternalItem


async def search(query: str, max_results: int) -> list[ExternalItem]:
    raise NotImplementedError("MedlinePlus search is not written yet")
