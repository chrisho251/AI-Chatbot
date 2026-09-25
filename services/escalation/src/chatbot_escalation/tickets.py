"""Ticket lifecycle. Stub owned by Lane A.

Purpose
Appendix C.2. Log the full question, retrieved context and confidence for expert review, notify the
on duty expert in real time, and track escalation rate and expert response time.

What to build
open_ticket stores the ticket in ops.escalation_tickets with the question encrypted, picks the
expert with rota.on_duty and sends notifier.notify. When nobody is on duty, fall back to the course
coordinator. answer stores the expert answer and answered_at, the gateway then serves it to the
student. The expert can also propose the item for the golden set or a corpus correction.
Record EXPERT_RESPONSE from chatbot_common.metrics when an answer arrives.

How to test
Use make_test_platform and a fake notifier. Open, answer and read back one ticket.
"""

from chatbot_contracts.base import Model
from chatbot_contracts.escalation import EscalationTicket


class ExpertAnswer(Model):
    expert: str
    answer: str
    propose_golden: bool = False


async def open_ticket(ticket: EscalationTicket) -> EscalationTicket:
    raise NotImplementedError("opening tickets is not written yet")


async def get_by_request(request_id: str) -> EscalationTicket:
    raise NotImplementedError("reading tickets is not written yet")


async def answer(ticket_id: str, expert_answer: ExpertAnswer) -> EscalationTicket:
    raise NotImplementedError("answering tickets is not written yet")
