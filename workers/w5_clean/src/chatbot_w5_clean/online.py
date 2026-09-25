"""Clean text at answer time. Stub owned by Lane B.

Purpose
Clean the student question, text read from an upload, or a fetched external web page before any
model sees it. Appendix A.4 asks W5 to clean user submitted and retrieved content.

Input
A CleanRequest. origin tells where the text came from, question, upload or external.

Output
A CleanResult. Set dropped to true when the injection scan finds instructions in external or
uploaded text, so the orchestrator never passes it to W8. Questions are never dropped here,
the gateway guard already decided they are safe.

What to build
normalize.normalize, then pii.scrub, then injection.scan for origins upload and external.
Use web.extract_text first when origin is external and the text is HTML.

How to test
Parametrize over the three origins with samples.sample_clean_request and assert the flags.
"""

from chatbot_contracts.query import CleanRequest, CleanResult


async def clean_text(request: CleanRequest) -> CleanResult:
    raise NotImplementedError("online cleaning is not written yet")
