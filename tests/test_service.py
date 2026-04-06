import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from riddle.models import RiddleResult
from riddle.service import RiddleService


@pytest.fixture
def service():
    return RiddleService()


def _mock_run(output: dict) -> MagicMock:
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout = json.dumps(output)
    return mock


def test_generate_riddle_success(service, tmp_path):
    output = {
        "question": "食べるほど減るのに、食べないと増えるものは？",
        "answer": "食欲",
        "pattern": "paradox",
        "score": {"uniqueness": True, "single_paradox": True, "observation_based": True},
        "attempts": 2,
    }
    output_file = tmp_path / "out.txt"
    output_file.write_text(json.dumps(output))

    with patch("riddle.service.subprocess.run", return_value=_mock_run(output)) as mock_run:
        with patch("riddle.service.Path") as mock_path_cls:
            mock_path_cls.return_value = output_file
            result = service.generate_riddle()

    assert isinstance(result, RiddleResult)
    assert result.answer == "食欲"
    assert result.attempts == 2


def test_generate_riddle_sets_codex_home(service, tmp_path):
    output = {
        "question": "q", "answer": "a", "pattern": "pun",
        "score": {"uniqueness": True, "single_paradox": True, "observation_based": True},
        "attempts": 1,
    }
    output_file = tmp_path / "out.txt"
    output_file.write_text(json.dumps(output))

    with patch("riddle.service.subprocess.run", return_value=_mock_run(output)) as mock_run:
        with patch("riddle.service.Path") as mock_path_cls:
            mock_path_cls.return_value = output_file
            service.generate_riddle()

    call_kwargs = mock_run.call_args
    env = call_kwargs.kwargs.get("env") or {}
    assert "CODEX_HOME" in env
    assert ".codex-home" in env["CODEX_HOME"]


def test_generate_riddle_max_retries(service, tmp_path):
    output = {"error": "max_retries_exceeded", "attempts": 5}
    output_file = tmp_path / "out.txt"
    output_file.write_text(json.dumps(output))

    with patch("riddle.service.subprocess.run", return_value=_mock_run(output)):
        with patch("riddle.service.Path") as mock_path_cls:
            mock_path_cls.return_value = output_file
            with pytest.raises(RuntimeError, match="max_retries_exceeded"):
                service.generate_riddle()
