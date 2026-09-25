from fastapi.testclient import TestClient

from chatbot_contracts import samples
from chatbot_contracts.routes import GENERATE, GENERATE_STREAM
from chatbot_w8_gen.serve import app

CASES = [
    (GENERATE, samples.sample_generation_request()),
    (GENERATE_STREAM, samples.sample_generation_request()),
]


def test_health():
    assert TestClient(app).get("/health").status_code == 200


def test_routes_accept_their_contract():
    client = TestClient(app)
    for endpoint, request in CASES:
        response = client.post(endpoint.path, json=request.model_dump(mode="json"))
        assert response.status_code not in (404, 405, 422), endpoint.path
