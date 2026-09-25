from fastapi.testclient import TestClient

from chatbot_gateway.serve import ASK_PATH, app


def test_health():
    assert TestClient(app).get("/health").status_code == 200


def test_ask_accepts_a_form_with_a_token():
    response = TestClient(app).post(
        ASK_PATH, data={"question": "What is a p value?"}, headers={"authorization": "Bearer x"}
    )
    assert response.status_code not in (404, 405, 422)
