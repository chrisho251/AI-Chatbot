"""Citation validation. Stub owned by Lane C.

Purpose
W8 may only cite chunks that W7 retrieved for this request. Anything else is a fabricated citation,
it is stripped and confidence drops.

Output
The kept citations and the number stripped. citation coverage for the confidence score is the share
of answer sentences that keep at least one citation.

How to test
A citation to a chunk id outside the retrieved set is stripped, external urls are kept only when
they came from W7 external search.
"""

from chatbot_contracts.external import ExternalItem
from chatbot_contracts.query import Citation, RetrievedChunk


def validate(
    citations: list[Citation],
    retrieved: list[RetrievedChunk],
    external: list[ExternalItem],
) -> tuple[list[Citation], int]:
    raise NotImplementedError("citation validation is not written yet")
