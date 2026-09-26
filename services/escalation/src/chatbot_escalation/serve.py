"""Entrypoint of the escalation service.

HANDLERS serves the two contract endpoints, OPEN_TICKET for the orchestrator and GET_TICKET for the
gateway, which reads late expert answers with it. The api service calls them in process.
router holds the public route POST /v1/tickets/{ticket_id}/answer, where the on duty expert answers.
It requires the expert role. The api service mounts it.
app serves both alone, for tests and for running the service in its own container.
"""

from fastapi import APIRouter

from chatbot_common.http import LocalHandler
from chatbot_common.service import add_contract_routes, create_app
from chatbot_contracts.escalation import EscalationTicket, TicketQuery
from chatbot_contracts.routes import GET_TICKET, OPEN_TICKET, Endpoint
from chatbot_escalation import tickets

ANSWER_PATH = "/v1/tickets/{ticket_id}/answer"


async def get_ticket(query: TicketQuery) -> EscalationTicket:
    return await tickets.get_by_request(query.request_id)


HANDLERS: dict[Endpoint, LocalHandler] = {
    OPEN_TICKET: tickets.open_ticket,
    GET_TICKET: get_ticket,
}

router = APIRouter()


@router.post(ANSWER_PATH, response_model=EscalationTicket)
async def answer_ticket(ticket_id: str, answer: tickets.ExpertAnswer) -> EscalationTicket:
    return await tickets.answer(ticket_id, answer)


app = create_app("escalation")
add_contract_routes(app, HANDLERS)
app.include_router(router)
