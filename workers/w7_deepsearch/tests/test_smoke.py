import pytest
from fastapi.testclient import TestClient

from chatbot_contracts import samples
from chatbot_contracts.routes import ALL_ENDPOINTS, EXTERNAL_SEARCH, RETRIEVE
from chatbot_w7_deepsearch import job
from chatbot_w7_deepsearch.allowlist import is_allowed
from chatbot_w7_deepsearch.serve import HANDLERS, app

CASES = [
    (RETRIEVE, samples.sample_retrieval_request()),
    (EXTERNAL_SEARCH, samples.sample_external_search_request()),
]


def test_health():
    assert TestClient(app).get("/health").status_code == 200


def test_routes_accept_their_contract():
    client = TestClient(app)
    for endpoint, request in CASES:
        response = client.post(endpoint.path, json=request.model_dump(mode="json"))
        assert response.status_code not in (404, 405, 422), endpoint.path


def test_job_needs_a_course_and_topics():
    with pytest.raises(SystemExit):
        job.main([])


@pytest.mark.parametrize(
    ("url", "allowed"),
    [
        ("https://openstax.org/books/x", True),
        ("https://math.libretexts.org/Bookshelves/Statistics", True),
        ("https://evil-openstax.org/x", False),
        ("https://example.com", False),
    ],
)
def test_allowlist(url, allowed):
    assert is_allowed(url) is allowed


def test_handlers_cover_every_w7_deepsearch_endpoint():
    assert set(HANDLERS) == {e for e in ALL_ENDPOINTS if e.service == "w7_deepsearch"}
