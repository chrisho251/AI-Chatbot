from fastapi.testclient import TestClient

from chatbot_contracts import samples
from chatbot_contracts.routes import OPEN_TICKET
from chatbot_escalation.serve import app


def test_health():
    assert TestClient(app).get("/health").status_code == 200


def test_open_ticket_accepts_the_contract():
    ticket = samples.sample_escalation_ticket()
    response = TestClient(app).post(OPEN_TICKET.path, json=ticket.model_dump(mode="json"))
    assert response.status_code not in (404, 405, 422)
