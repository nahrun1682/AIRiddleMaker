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
    assert "score_riddle" in prompt


def test_generate_riddle_passes_mcp_config_via_cli(service, tmp_path):
    """codex exec must receive -c flag configuring the scorer MCP server."""
    output = {
        "question": "q", "answer": "a", "pattern": "pun",
        "score": {
            "uniqueness": True, "single_paradox": True,
            "observation_based": True, "strict_score": 9.6,
            "passed": True, "reason": "r", "strict_review": "s",
        },
        "attempts": 1,
    }
    output_file = tmp_path / "out.txt"
    output_file.write_text(json.dumps(output))

    with patch("riddle.service.subprocess.run", return_value=_mock_run(output)) as mock_run, \
         patch("riddle.service._OUTPUT_FILE", output_file):
        service.generate_riddle(scorer_port=19120, scorer_model="gpt-5.4")

    cmd = mock_run.call_args[0][0]
    # Find all -c arguments and their values
    c_values = []
    for i, arg in enumerate(cmd):
        if arg == "-c" and i + 1 < len(cmd):
            c_values.append(cmd[i + 1])

    # Must have MCP server URL config
    mcp_config = [v for v in c_values if "mcp_servers" in v and "19120" in v]
    assert mcp_config, f"No MCP server config in -c flags: {c_values}"


def test_stale_items_includes_tmp_and_sessions():
    """Old tmp/ and sessions/ dirs should be cleaned on each sync."""
    from riddle.service import _STALE_ITEMS
    assert "tmp" in _STALE_ITEMS
    assert "sessions" in _STALE_ITEMS


def test_generate_riddle_starts_and_stops_scorer(service, tmp_path):
    """service starts scorer server before codex exec and stops it after."""
    output = {
        "question": "q", "answer": "a", "pattern": "paradox",
        "score": {
            "uniqueness": True, "single_paradox": True,
            "observation_based": True, "strict_score": 9.6,
            "passed": True, "reason": "r", "strict_review": "s",
        },
        "attempts": 1,
    }
    output_file = tmp_path / "out.txt"
    output_file.write_text(json.dumps(output))

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    with patch("riddle.service.subprocess.run", return_value=_mock_run(output)), \
         patch("riddle.service._OUTPUT_FILE", output_file), \
         patch("riddle.service.subprocess.Popen", return_value=mock_proc) as mock_popen, \
         patch("riddle.service.urllib.request.urlopen"):
        service.generate_riddle(scorer_port=19120, scorer_model="gpt-5.4")

    mock_popen.assert_called_once()
    popen_cmd = mock_popen.call_args[0][0]
    assert "scorer_server" in " ".join(str(x) for x in popen_cmd)
    mock_proc.terminate.assert_called_once()


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
