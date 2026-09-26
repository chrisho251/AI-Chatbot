"""The ask flow of the gateway. Stub owned by Lane C.

Purpose
Step 1 and step 10 of the query path in ARCHITECTURE.md section 5.

What to build, in this order
Record t0.
auth.authenticate the bearer token and require the student role.
limits.admit the pseudonymized user, answer 429 or 503 when over the limits.
pseudonym.pseudonymize the student id. Fail closed when the keys are unavailable.
Use the conversation id from the form, or start a new one for a first question.
uploads.store_attachment when a file is present.
Start guard.check as a task and the orchestrator stream at the same time. Forward an AskRequest to
the orchestrator with shared_client().stream and routes.ANSWER. Hold every event until the guard
verdict arrives. When the question is unsafe, cancel the stream, answer one error StreamEvent and
write an ops.guard_events row. Nothing reaches the student before the verdict.
Relay every StreamEvent with the conversation id set, record t_first_token at the first answer
delta and t_last_byte at the end, then write the ops.request_facts row.
Record FIRST_TOKEN, RESPONSE and REQUESTS from chatbot_common.metrics, see docs/MONITORING.md.

fetch_late_answer checks that the caller owns the request, then reads the ticket with
shared_client().call and routes.GET_TICKET and returns it once an expert answered.

How to test
Build a ContractClient with local handlers that return sample stream events, and fake the guard
with a slow unsafe verdict to check that no event leaks. Fake Keycloak by signing a token with a
local key in the test.
"""

from fastapi import UploadFile
from fastapi.responses import StreamingResponse

from chatbot_contracts.escalation import EscalationTicket


async def handle_ask(
    question: str, conversation_id: str | None, file: UploadFile | None, authorization: str
) -> StreamingResponse:
    raise NotImplementedError("the ask flow is not written yet")


async def fetch_late_answer(request_id: str, authorization: str) -> EscalationTicket:
    raise NotImplementedError("late answers are not written yet")
