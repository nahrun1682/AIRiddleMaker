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
    "structural_soundness": True,
    "concrete_grounding": True,
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


def test_score_operation_id_is_score_riddle():
    """MCP tool name must be exactly 'score_riddle' for Codex to discover it."""
    from riddle.scorer_server import create_app
    from fastapi.openapi.utils import get_openapi

    app = create_app(model="gpt-5.4", api_key="test-key")
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    score_op = schema["paths"]["/score"]["post"]
    assert score_op["operationId"] == "score_riddle"


@patch("riddle.scorer_server.search_riddle_evidence")
def test_score_injects_search_evidence_into_prompt(mock_search, client):
    """検索結果がLLMプロンプトに注入されることを確認."""
    mock_search.return_value = {
        "hit_count": 500,
        "snippets": ["春雨のなぞなぞ — Q:空から降る A:春雨 (https://example.com)"],
    }
    with patch("riddle.scorer_server._openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            PASSING_SCORE
        )
        client.post(
            "/score",
            json={"question": "空から降るのにすするものは？", "answer": "春雨"},
        )

    call_args = mock_client.chat.completions.create.call_args
    user_msg = call_args.kwargs["messages"][1]["content"]
    assert "検索ヒット数" in user_msg
    assert "500" in user_msg
    assert "春雨のなぞなぞ" in user_msg


@patch("riddle.scorer_server.search_riddle_evidence")
def test_score_works_when_search_fails(mock_search, client):
    """検索が失敗しても採点は続行する."""
    mock_search.return_value = None
    with patch("riddle.scorer_server._openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            PASSING_SCORE
        )
        resp = client.post("/score", json={"question": "q", "answer": "a"})

    assert resp.status_code == 200
    call_args = mock_client.chat.completions.create.call_args
    user_msg = call_args.kwargs["messages"][1]["content"]
    assert "検索不可" in user_msg


@patch("riddle.scorer_server.search_riddle_evidence")
def test_score_no_search_hits(mock_search, client):
    """検索0件の場合もプロンプトに反映."""
    mock_search.return_value = {"hit_count": 0, "snippets": []}
    with patch("riddle.scorer_server._openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            PASSING_SCORE
        )
        client.post("/score", json={"question": "q", "answer": "a"})

    call_args = mock_client.chat.completions.create.call_args
    user_msg = call_args.kwargs["messages"][1]["content"]
    assert "検索ヒット数: 0" in user_msg
