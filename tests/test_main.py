from unittest.mock import MagicMock, patch

import pytest

from riddle.main import main
from riddle.models import RiddleResult, ScoreDetail


def _make_result(**kwargs) -> RiddleResult:
    defaults = dict(
        question="テスト問題",
        answer="テスト答え",
        pattern="pun",
        score=ScoreDetail(uniqueness=True, single_paradox=True, observation_based=True),
        attempts=1,
    )
    return RiddleResult(**(defaults | kwargs))


def test_main_outputs_riddle(capsys):
    with patch("riddle.main.RiddleService") as MockService:
        MockService.return_value.generate_riddle.return_value = _make_result()
        main([])

    captured = capsys.readouterr()
    assert "テスト問題" in captured.out
    assert "テスト答え" in captured.out


def test_main_pattern_option(capsys):
    with patch("riddle.main.RiddleService") as MockService:
        MockService.return_value.generate_riddle.return_value = _make_result(pattern="paradox")
        main(["--pattern", "paradox"])

    MockService.return_value.generate_riddle.assert_called_once_with(pattern="paradox")


def test_main_error_exits(capsys):
    with patch("riddle.main.RiddleService") as MockService:
        MockService.return_value.generate_riddle.side_effect = RuntimeError("max_retries_exceeded")
        with pytest.raises(SystemExit) as exc_info:
            main([])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "max_retries_exceeded" in captured.err
