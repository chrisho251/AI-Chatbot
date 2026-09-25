"""Turn citation markers in the answer into Citation records. Stub owned by Lane C.

What to build
Markers look like [1] and point at the numbered contexts of the prompt. Map each to the chunk id,
document version and page of that context, or to the url of an external context. Unknown numbers
are dropped here, the orchestrator validates the rest.

How to test
An answer with [1] and [3] and two contexts gives one citation and drops the unknown number.
"""

from chatbot_contracts.query import Citation, GenerationRequest


def parse(answer: str, request: GenerationRequest) -> list[Citation]:
    raise NotImplementedError("citation parsing is not written yet")
