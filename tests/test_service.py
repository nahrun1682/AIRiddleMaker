import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from riddle.models import RiddleResult
from riddle.service import RiddleService


@pytest.fixture
def service(tmp_path):
    with patch.object(RiddleService, "_sync_runtime_home"):
        svc = RiddleService(codex_home=tmp_path / ".codex-home")
    svc.codex_home = tmp_path / ".codex-home"
    svc.codex_home.mkdir(parents=True, exist_ok=True)
    return svc


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
        "score": {
            "uniqueness": True,
            "single_paradox": True,
            "observation_based": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 2,
    }
    output_file = tmp_path / "out.txt"
    output_file.write_text(json.dumps(output))

    with patch("riddle.service.subprocess.run", return_value=_mock_run(output)) as mock_run, \
         patch("riddle.service._OUTPUT_FILE", output_file):
        result = service.generate_riddle()

    assert isinstance(result, RiddleResult)
    assert result.answer == "食欲"
    assert result.attempts == 2


def test_generate_riddle_sets_codex_home(service, tmp_path):
    output = {
        "question": "q", "answer": "a", "pattern": "pun",
        "score": {
            "uniqueness": True,
            "single_paradox": True,
            "observation_based": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }
    output_file = tmp_path / "out.txt"
    output_file.write_text(json.dumps(output))

    with patch("riddle.service.subprocess.run", return_value=_mock_run(output)) as mock_run, \
         patch("riddle.service._OUTPUT_FILE", output_file):
        service.generate_riddle()

    call_kwargs = mock_run.call_args
    env = call_kwargs.kwargs.get("env") or {}
    cmd = call_kwargs.args[0]
    assert "CODEX_HOME" in env
    assert ".codex-home" in env["CODEX_HOME"]
    assert "-C" in cmd
    assert env["CODEX_HOME"] in cmd
    assert "-m" in cmd
    assert "gpt-5.3-codex" in cmd
    assert "-c" in cmd
    assert 'model_reasoning_effort="medium"' in cmd


def test_generate_riddle_includes_theme_in_prompt(service, tmp_path):
    output = {
        "question": "q", "answer": "a", "pattern": "pun",
        "score": {
            "uniqueness": True,
            "single_paradox": True,
            "observation_based": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }
    output_file = tmp_path / "out.txt"
    output_file.write_text(json.dumps(output))

    with patch("riddle.service.subprocess.run", return_value=_mock_run(output)) as mock_run, \
         patch("riddle.service._OUTPUT_FILE", output_file):
        service.generate_riddle(theme="食べ物")

    cmd = mock_run.call_args[0][0]
    prompt = cmd[-1]
    assert "食べ物" in prompt


def test_generate_riddle_includes_max_retries_in_prompt(service, tmp_path):
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "pun",
        "score": {
            "uniqueness": True,
            "single_paradox": True,
            "observation_based": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }
    output_file = tmp_path / "out.txt"
    output_file.write_text(json.dumps(output))

    with patch("riddle.service.subprocess.run", return_value=_mock_run(output)) as mock_run, \
         patch("riddle.service._OUTPUT_FILE", output_file):
        service.generate_riddle(max_retries=12)

    prompt = mock_run.call_args[0][0][-1]
    assert "最大12回" in prompt


def test_generate_riddle_includes_scorer_subagent_instruction(service, tmp_path):
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "pun",
        "score": {
            "uniqueness": True,
            "single_paradox": True,
            "observation_based": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }
    output_file = tmp_path / "out.txt"
    output_file.write_text(json.dumps(output))

    with patch("riddle.service.subprocess.run", return_value=_mock_run(output)) as mock_run, \
         patch("riddle.service._OUTPUT_FILE", output_file):
        service.generate_riddle()

    prompt = mock_run.call_args[0][0][-1]
    assert "サブエージェント `scorer`" in prompt


def test_generate_riddle_validates_strict_threshold(service, tmp_path):
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "pun",
        "score": {
            "uniqueness": True,
            "single_paradox": True,
            "observation_based": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }
    output_file = tmp_path / "out.txt"
    output_file.write_text(json.dumps(output))

    with patch("riddle.service.subprocess.run", return_value=_mock_run(output)), \
         patch("riddle.service._OUTPUT_FILE", output_file):
        with pytest.raises(RuntimeError, match="strict_threshold"):
            service.generate_riddle(strict_threshold=9.7)


def test_generate_riddle_requires_reason_fields_when_enabled(service, tmp_path):
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "pun",
        "score": {
            "uniqueness": True,
            "single_paradox": True,
            "observation_based": True,
            "strict_score": 9.6,
            "passed": True,
        },
        "attempts": 1,
    }
    output_file = tmp_path / "out.txt"
    output_file.write_text(json.dumps(output))

    with patch("riddle.service.subprocess.run", return_value=_mock_run(output)), \
         patch("riddle.service._OUTPUT_FILE", output_file):
        with pytest.raises(RuntimeError, match="reason/strict_review"):
            service.generate_riddle(require_reason_fields=True)


def test_generate_riddle_max_retries(service, tmp_path):
    output = {"error": "max_retries_exceeded", "attempts": 5}
    output_file = tmp_path / "out.txt"
    output_file.write_text(json.dumps(output))

    with patch("riddle.service.subprocess.run", return_value=_mock_run(output)), \
         patch("riddle.service._OUTPUT_FILE", output_file):
        with pytest.raises(RuntimeError, match="max_retries_exceeded"):
            service.generate_riddle()
