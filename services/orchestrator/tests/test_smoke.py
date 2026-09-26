from fastapi.testclient import TestClient

from chatbot_contracts import samples
from chatbot_contracts.routes import ALL_ENDPOINTS, ANSWER
from chatbot_orchestrator.serve import HANDLERS, app


def test_health():
    assert TestClient(app).get("/health").status_code == 200


def test_answer_route_accepts_the_contract():
    response = TestClient(app).post(
        ANSWER.path, json=samples.sample_ask_request().model_dump(mode="json")
    )
    assert response.status_code not in (404, 405, 422)


def test_handlers_cover_every_orchestrator_endpoint():
    assert set(HANDLERS) == {e for e in ALL_ENDPOINTS if e.service == "orchestrator"}
