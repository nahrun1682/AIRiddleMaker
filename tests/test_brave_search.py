"""Tests for brave_search module."""

from unittest.mock import MagicMock, patch

from riddle.brave_search import search_riddle_evidence

BRAVE_RESPONSE_HIT = {
    "query": {"original": "春雨 なぞなぞ"},
    "web": {
        "totalEstimatedMatches": 1234,
        "results": [
            {
                "title": "春雨のなぞなぞ - なぞなぞランド",
                "url": "https://example.com/nazonazo/harusame",
                "description": "Q: 空から降ってくるのにすするものは？ A: 春雨",
            },
            {
                "title": "食べ物なぞなぞ集",
                "url": "https://example.com/food",
                "description": "春雨に関する問題が多数あります。",
            },
        ],
    },
}

BRAVE_RESPONSE_NO_HIT = {
    "query": {"original": "ガスメーター なぞなぞ"},
    "web": {
        "totalEstimatedMatches": 0,
        "results": [],
    },
}

BRAVE_RESPONSE_NO_WEB = {
    "query": {"original": "テスト なぞなぞ"},
}


def _mock_get(json_data: dict, status_code: int = 200) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    mock_resp.raise_for_status.return_value = None
    if status_code >= 400:
        mock_resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return mock_resp


class TestSearchRiddleEvidence:
    @patch("riddle.brave_search.requests.get")
    def test_returns_hit_count_and_snippets(self, mock_get):
        mock_get.return_value = _mock_get(BRAVE_RESPONSE_HIT)
        result = search_riddle_evidence("春雨", api_key="test-key")

        assert result["hit_count"] == 1234
        assert len(result["snippets"]) == 2
        assert "春雨のなぞなぞ" in result["snippets"][0]
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["params"]["q"] == "春雨 なぞなぞ"

    @patch("riddle.brave_search.requests.get")
    def test_no_hits_returns_zero(self, mock_get):
        mock_get.return_value = _mock_get(BRAVE_RESPONSE_NO_HIT)
        result = search_riddle_evidence("ガスメーター", api_key="test-key")

        assert result["hit_count"] == 0
        assert result["snippets"] == []

    @patch("riddle.brave_search.requests.get")
    def test_no_web_key_returns_zero(self, mock_get):
        mock_get.return_value = _mock_get(BRAVE_RESPONSE_NO_WEB)
        result = search_riddle_evidence("テスト", api_key="test-key")

        assert result["hit_count"] == 0
        assert result["snippets"] == []

    @patch("riddle.brave_search.requests.get")
    def test_api_error_returns_none(self, mock_get):
        mock_get.return_value = _mock_get({}, status_code=500)
        result = search_riddle_evidence("春雨", api_key="test-key")

        assert result is None

    @patch("riddle.brave_search.requests.get")
    def test_network_error_returns_none(self, mock_get):
        mock_get.side_effect = ConnectionError("timeout")
        result = search_riddle_evidence("春雨", api_key="test-key")

        assert result is None

    @patch("riddle.brave_search.requests.get")
    def test_no_api_key_returns_none(self, mock_get):
        result = search_riddle_evidence("春雨", api_key="")

        assert result is None
        mock_get.assert_not_called()
