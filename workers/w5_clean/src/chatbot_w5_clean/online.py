"""Clean text at answer time.

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

import asyncio
import re

from chatbot_contracts.enums import CleanOrigin
from chatbot_contracts.query import CleanRequest, CleanResult
from chatbot_w5_clean import injection, normalize, pii, web

_HTML_RE = re.compile(r"<\s*(html|body|article|head|main|div|p|h\d|table)", re.IGNORECASE)


def _looks_like_html(text: str) -> bool:
    return bool(_HTML_RE.search(text))


async def clean_text(request: CleanRequest) -> CleanResult:
    """Clean the text of a request based on its origin."""
    text = request.text
    origin = request.origin

    if origin == CleanOrigin.EXTERNAL:
        if _looks_like_html(text):
            text = web.extract_text(text)
        if not text.strip():
            return CleanResult(request_id=request.request_id, text="", dropped=True)

    text = normalize.normalize(text)
    scrub_result = pii.scrub(text)
    text = scrub_result.text

    injection_hits = 0
    dropped = False
    if origin in (CleanOrigin.UPLOAD, CleanOrigin.EXTERNAL):
        scan_result = await asyncio.to_thread(injection.scan, text)
        injection_hits = scan_result.hits
        if injection_hits > 0:
            dropped = True

    return CleanResult(
        request_id=request.request_id,
        text=text,
        pii_hits=scrub_result.hits,
        injection_hits=injection_hits,
        dropped=dropped,
    )
