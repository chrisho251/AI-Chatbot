from fastapi.testclient import TestClient

from chatbot_contracts import samples
from chatbot_contracts.routes import ALL_ENDPOINTS, GET_TICKET, OPEN_TICKET
from chatbot_escalation.serve import ANSWER_PATH, HANDLERS, app

CASES = [
    (OPEN_TICKET, samples.sample_escalation_ticket()),
    (GET_TICKET, samples.sample_ticket_query()),
]


def test_health():
    assert TestClient(app).get("/health").status_code == 200


def test_routes_accept_their_contract():
    client = TestClient(app)
    for endpoint, request in CASES:
        response = client.post(endpoint.path, json=request.model_dump(mode="json"))
        assert response.status_code not in (404, 405, 422), endpoint.path


def test_expert_answer_route_exists():
    path = ANSWER_PATH.format(ticket_id="ticket-0001")
    response = TestClient(app).post(path, json={"expert": "e1", "answer": "Use a t interval."})
    assert response.status_code not in (404, 405, 422)


def test_handlers_cover_every_escalation_endpoint():
    assert set(HANDLERS) == {e for e in ALL_ENDPOINTS if e.service == "escalation"}
