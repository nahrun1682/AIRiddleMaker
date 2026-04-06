import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _mock_openai_response(content: dict) -> MagicMock:
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(content)
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


PASSING_SCORE = {
    "uniqueness": True,
    "single_paradox": True,
    "observation_based": True,
    "strict_score": 7.5,
    "passed": True,
    "reason": "良問",
    "strict_review": "厳しく評価：7.5/10点",
}


@pytest.fixture
def client():
    from riddle.scorer_server import create_app

    app = create_app(model="gpt-5.4", api_key="test-key")
    return TestClient(app)


def test_score_endpoint_returns_score(client):
    with patch("riddle.scorer_server._openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            PASSING_SCORE
        )
        resp = client.post("/score", json={"question": "問題文", "answer": "答え"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["strict_score"] == 7.5
    assert data["passed"] is True


def test_score_endpoint_rejects_empty_question(client):
    resp = client.post("/score", json={"question": "", "answer": "答え"})
    assert resp.status_code == 422


def test_score_endpoint_rejects_missing_answer(client):
    resp = client.post("/score", json={"question": "問題文"})
    assert resp.status_code == 422


def test_mcp_endpoint_mounted(client):
    """The /mcp path should be mounted (not 404)."""
    resp = client.get("/mcp")
    assert resp.status_code != 404


def test_score_sends_system_prompt(client):
    """Verify the system prompt from scorer_prompt.md is sent to OpenAI."""
    with patch("riddle.scorer_server._openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            PASSING_SCORE
        )
        client.post("/score", json={"question": "q", "answer": "a"})

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    system_msg = messages[0]["content"]
    assert "採点エージェント" in system_msg
    assert "strict_score" in system_msg
