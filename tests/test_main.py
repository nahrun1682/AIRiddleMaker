from unittest.mock import patch

import pytest

from riddle.main import main
from riddle.models import RiddleResult, ScoreDetail


def _make_result(**kwargs) -> RiddleResult:
    defaults = dict(
        question="テスト問題",
        answer="テスト答え",
        pattern="pun",
        score=ScoreDetail(
            uniqueness=True,
            single_paradox=True,
            observation_based=True,
            strict_score=9.6,
            passed=True,
            reason="既視感がある",
            strict_review="厳しく評価：9.6/10点（高品質）\n\n### 良い点\n- 明快\n\n### 厳しい点\n- やや定番\n\n### 類似例（調べた場合）\n- 類似あり\n\n**総評**\n良作",
        ),
        attempts=1,
    )
    return RiddleResult(**(defaults | kwargs))


def test_main_outputs_riddle(capsys):
    with patch("riddle.main.RiddleService") as MockService, patch("builtins.input", return_value=""):
        MockService.return_value.generate_riddle.return_value = _make_result()
        main([])

    captured = capsys.readouterr()
    assert "テスト問題" in captured.out
    assert "テスト答え" in captured.out
    assert "厳格スコア: 9.6" in captured.out
    assert "判定: passed=True" in captured.out
    assert "既視感がある" in captured.out
    assert "厳しく評価：9.6/10点" in captured.out


def test_main_pattern_option(capsys, monkeypatch):
    monkeypatch.setenv("RIDDLE_CONFIG_FILE", "/tmp/nonexistent-riddle-test.toml")
    with patch("riddle.main.RiddleService") as MockService, patch("builtins.input", return_value=""):
        MockService.return_value.generate_riddle.return_value = _make_result(pattern="paradox")
        main(["--pattern", "paradox"])

    MockService.return_value.generate_riddle.assert_called_once_with(
        pattern="paradox",
        theme=None,
        max_retries=10,
        trace=False,
        model="gpt-5.3-codex",
        reasoning_effort="medium",
        strict_threshold=6.0,
        require_reason_fields=True,
        scorer_port=19120,
        scorer_model="gpt-5.4",
    )


def test_main_prompts_for_theme_when_not_given(capsys, monkeypatch):
    monkeypatch.setenv("RIDDLE_CONFIG_FILE", "/tmp/nonexistent-riddle-test.toml")
    with patch("riddle.main.RiddleService") as MockService, patch("builtins.input", return_value="食べ物"):
        MockService.return_value.generate_riddle.return_value = _make_result()
        main([])

    MockService.return_value.generate_riddle.assert_called_once_with(
        pattern=None,
        theme="食べ物",
        max_retries=10,
        trace=False,
        model="gpt-5.3-codex",
        reasoning_effort="medium",
        strict_threshold=6.0,
        require_reason_fields=True,
        scorer_port=19120,
        scorer_model="gpt-5.4",
    )


def test_main_max_retries_option(capsys, monkeypatch):
    monkeypatch.setenv("RIDDLE_CONFIG_FILE", "/tmp/nonexistent-riddle-test.toml")
    with patch("riddle.main.RiddleService") as MockService, patch("builtins.input", return_value=""):
        MockService.return_value.generate_riddle.return_value = _make_result()
        main(["--max-retries", "15"])

    MockService.return_value.generate_riddle.assert_called_once_with(
        pattern=None,
        theme=None,
        max_retries=15,
        trace=False,
        model="gpt-5.3-codex",
        reasoning_effort="medium",
        strict_threshold=6.0,
        require_reason_fields=True,
        scorer_port=19120,
        scorer_model="gpt-5.4",
    )


def test_main_trace_option(monkeypatch):
    monkeypatch.setenv("RIDDLE_CONFIG_FILE", "/tmp/nonexistent-riddle-test.toml")
    with patch("riddle.main.RiddleService") as MockService, patch("builtins.input", return_value=""):
        MockService.return_value.generate_riddle.return_value = _make_result()
        main(["--trace"])

    MockService.return_value.generate_riddle.assert_called_once_with(
        pattern=None,
        theme=None,
        max_retries=10,
        trace=True,
        model="gpt-5.3-codex",
        reasoning_effort="medium",
        strict_threshold=6.0,
        require_reason_fields=True,
        scorer_port=19120,
        scorer_model="gpt-5.4",
    )


def test_main_uses_config_values(capsys, monkeypatch):
    monkeypatch.setenv("RIDDLE_CONFIG_FILE", "/tmp/nonexistent-riddle.toml")
    with patch("riddle.main.load_riddle_config") as mock_load, patch(
        "riddle.main.RiddleService"
    ) as MockService, patch("builtins.input", return_value=""):
        from riddle.config import RiddleConfig

        mock_load.return_value = RiddleConfig(
            model="gpt-5.4",
            reasoning_effort="high",
            max_retries=15,
            strict_threshold=9.7,
            require_reason_fields=False,
            trace_default=True,
        )
        MockService.return_value.generate_riddle.return_value = _make_result()
        main([])

    MockService.return_value.generate_riddle.assert_called_once_with(
        pattern=None,
        theme=None,
        max_retries=15,
        trace=True,
        model="gpt-5.4",
        reasoning_effort="high",
        strict_threshold=9.7,
        require_reason_fields=False,
        scorer_port=19120,
        scorer_model="gpt-5.4",
    )


def test_main_theme_shown_in_output(capsys):
    with patch("riddle.main.RiddleService") as MockService, patch("builtins.input", return_value="動物"):
        MockService.return_value.generate_riddle.return_value = _make_result()
        main([])

    captured = capsys.readouterr()
    assert "動物" in captured.out


def test_main_error_exits(capsys):
    with patch("riddle.main.RiddleService") as MockService, patch("builtins.input", return_value=""):
        MockService.return_value.generate_riddle.side_effect = RuntimeError("max_retries_exceeded")
        with pytest.raises(SystemExit) as exc_info:
            main([])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "max_retries_exceeded" in captured.err
