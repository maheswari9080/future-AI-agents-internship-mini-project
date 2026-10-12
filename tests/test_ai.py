from unittest.mock import patch, AsyncMock
import httpx


def test_ai_status_endpoint(client):
    resp = client.get("/ai/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "available" in data
    assert "model" in data


def test_reject_short_ai_question(client):
    resp = client.post("/ai/ask", json={"question": "hi"})
    assert resp.status_code == 422


def test_reject_empty_ai_question(client):
    resp = client.post("/ai/ask", json={"question": "   "})
    assert resp.status_code == 422


def test_ai_ask_fallback_when_ollama_offline(client):
    # Asking a standard counting question when Ollama is offline returns deterministic answer
    resp = client.post("/ai/ask", json={"question": "How many students are registered?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "student" in data["answer"].lower()
    assert "deterministic" in data["source"]


@patch("httpx.AsyncClient.get")
@patch("httpx.AsyncClient.post")
def test_ai_ask_with_mocked_ollama_success(mock_post, mock_get, client):
    # Mock Ollama status check as available
    mock_get.return_value = AsyncMock(
        status_code=200,
        json=lambda: {"version": "0.1.30"},
    )
    # Mock Ollama generation response
    mock_post.return_value = AsyncMock(
        status_code=200,
        json=lambda: {"response": "Mocked AI: There are currently 0 students enrolled."},
    )

    resp = client.post("/ai/ask", json={"question": "Summarize student records"})
    assert resp.status_code == 200
    data = resp.json()
    assert "Mocked AI" in data["answer"]
    assert data["source"] == "ollama"
