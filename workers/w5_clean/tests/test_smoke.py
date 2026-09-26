import pytest
from fastapi.testclient import TestClient

from chatbot_contracts import samples
from chatbot_contracts.routes import ALL_ENDPOINTS, CLEAN
from chatbot_w5_clean import job
from chatbot_w5_clean.serve import HANDLERS, app

CASES = [(CLEAN, samples.sample_clean_request())]


def test_job_needs_run_and_document():
    with pytest.raises(SystemExit):
        job.main([])


def test_health():
    assert TestClient(app).get("/health").status_code == 200


def test_routes_accept_their_contract():
    client = TestClient(app)
    for endpoint, request in CASES:
        response = client.post(endpoint.path, json=request.model_dump(mode="json"))
        assert response.status_code not in (404, 405, 422), endpoint.path


def test_handlers_cover_every_w5_clean_endpoint():
    assert set(HANDLERS) == {e for e in ALL_ENDPOINTS if e.service == "w5_clean"}
