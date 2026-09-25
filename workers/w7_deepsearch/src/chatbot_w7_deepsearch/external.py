"""External search over allowlisted sources. Stub owned by Lane C.

Purpose
Appendix A.4 asks W7 to search external web sources for supplementary exercises and their answer
keys. It runs only after internal retrieval, when evidence is weak or the answer lands at L3.

What to build
The query arrives PII stripped. Query the sources in the sources package in parallel with a
timeout, drop any url that allowlist.is_allowed rejects, fetch and snapshot the pages into the
external bucket, send the HTML to W5 with origin external and drop pages W5 marks as dropped.
Queue every kept page with candidates.queue so an SME can add it to the corpus later.
Record the time spent, it feeds the external response time metric.

How to test
Fake every source and W5 with httpx MockTransport and fake_client, assert that a url outside the
allowlist never appears in the result.
"""

from chatbot_contracts.external import ExternalSearchRequest, ExternalSearchResult


async def search_external(request: ExternalSearchRequest) -> ExternalSearchResult:
    raise NotImplementedError("external search is not written yet")
