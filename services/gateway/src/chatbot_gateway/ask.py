"""The ask flow of the gateway. Stub owned by Lane C.

Purpose
Step 1 and step 10 of the query path in ARCHITECTURE.md section 5.

What to build, in this order
Record t0.
auth.authenticate the bearer token and require the student role.
limits.admit the pseudonymized user, answer 429 or 503 when over the limits.
pseudonym.pseudonymize the student id. Fail closed when Vault is down.
guard.check the question. When unsafe, answer one error StreamEvent and log obs.guard_events.
uploads.store_attachment when a file is present.
Forward an AskRequest to the orchestrator with ContractClient.stream and routes.ANSWER.
Relay every StreamEvent to the student, record t_first_token at the first answer delta and
t_last_byte at the end, then write the obs.request_facts row.
Record FIRST_TOKEN, RESPONSE and REQUESTS from chatbot_common.metrics, see docs/MONITORING.md.

fetch_late_answer checks that the caller owns the request, then reads the ticket from the escalation
service and returns it once an expert answered.

How to test
Fake the orchestrator with chatbot_common.testing.fake_client and a list of sample stream events.
Fake Keycloak by signing a token with a local key in the test.
"""

from fastapi import UploadFile
from fastapi.responses import StreamingResponse

from chatbot_contracts.escalation import EscalationTicket


async def handle_ask(
    question: str, file: UploadFile | None, authorization: str
) -> StreamingResponse:
    raise NotImplementedError("the ask flow is not written yet")


async def fetch_late_answer(request_id: str, authorization: str) -> EscalationTicket:
    raise NotImplementedError("late answers are not written yet")
