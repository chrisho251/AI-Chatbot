from fastapi.testclient import TestClient

from chatbot_api.serve import app, local_handlers
from chatbot_contracts.routes import ALL_ENDPOINTS, CALC, VISION
from chatbot_escalation.serve import ANSWER_PATH
from chatbot_gateway.serve import ASK_PATH, LATE_ANSWER_PATH


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok", "service": "api"}


def test_every_contract_endpoint_runs_in_process():
    assert set(local_handlers({})) == set(ALL_ENDPOINTS)


def test_a_url_override_moves_a_worker_out_of_process():
    handlers = local_handlers({"CHATBOT_W2_VISION_URL": "http://w2-vision:8000"})
    assert VISION not in handlers
    assert CALC in handlers


def test_only_public_routes_are_served_over_http():
    paths = set(app.openapi()["paths"])
    assert {ASK_PATH, LATE_ANSWER_PATH, ANSWER_PATH} <= paths
    assert not paths & {endpoint.path for endpoint in ALL_ENDPOINTS}
