"""The answer pipeline. Stub owned by Lane C.

Purpose
Steps 2 to 9 of the query path in ARCHITECTURE.md section 5. It yields StreamEvent records that the
gateway relays to the student.

What to build, in this order
Pin the serving corpus version from the platform registry alias serving.
If there are attachments call W2 for each image. Call W5 on the question and attachment text.
Call W6 for the query vector.
Call W7 retrieve. When sufficiency is below the floor, skip the first draft, search externally.
Stream W8 generate, forward answer delta events, validate citations with citations.validate.
Score with confidence.score and route with confidence.level.
At L3 send status.external_search, call W7 external, clean the pages with W5, regenerate with the
external context labelled unvetted, and score again.
Still L3, open a ticket with the escalation service and send status.expert_pending.
Log the interaction with interactions.record in every case.

Every call goes through ContractClient with an Endpoint from chatbot_contracts.routes.
Record CONFIDENCE, ESCALATIONS and EXTERNAL_RESPONSE from chatbot_common.metrics.

How to test
Build a ContractClient on chatbot_common.testing.fake_client with samples for every endpoint, then
make the retrieval sample weak to walk the L3 path. No other lane needs to be running.
"""

from collections.abc import AsyncIterator

from chatbot_common.http import ContractClient
from chatbot_contracts.escalation import StreamEvent
from chatbot_contracts.query import AskRequest


def answer(request: AskRequest, client: ContractClient | None = None) -> AsyncIterator[StreamEvent]:
    """Yield the events of one request. Write it as an async generator when implementing."""
    raise NotImplementedError("the answer pipeline is not written yet")
