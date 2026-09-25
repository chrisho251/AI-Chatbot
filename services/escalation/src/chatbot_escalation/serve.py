"""HTTP entrypoint of the escalation service.

POST /v1/tickets opens a ticket, the orchestrator is the caller.
GET /v1/tickets/{request_id} returns the ticket of a request, the gateway polls it for late answers.
POST /v1/tickets/{ticket_id}/answer lets the on duty expert answer, it requires the expert role.
"""

from chatbot_common.service import create_app
from chatbot_contracts.escalation import EscalationTicket
from chatbot_contracts.routes import OPEN_TICKET
from chatbot_escalation import tickets

TICKET_PATH = "/v1/tickets/{request_id}"
ANSWER_PATH = "/v1/tickets/{ticket_id}/answer"

app = create_app("escalation")


@app.post(OPEN_TICKET.path, response_model=EscalationTicket)
async def open_ticket(ticket: EscalationTicket) -> EscalationTicket:
    return await tickets.open_ticket(ticket)


@app.get(TICKET_PATH, response_model=EscalationTicket)
async def get_ticket(request_id: str) -> EscalationTicket:
    return await tickets.get_by_request(request_id)


@app.post(ANSWER_PATH, response_model=EscalationTicket)
async def answer_ticket(ticket_id: str, answer: tickets.ExpertAnswer) -> EscalationTicket:
    return await tickets.answer(ticket_id, answer)
