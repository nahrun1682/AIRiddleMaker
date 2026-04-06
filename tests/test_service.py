import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from riddle.models import RiddleResult
from riddle.service import RiddleService


@pytest.fixture
def service(tmp_path):
    svc = RiddleService(codex_home=tmp_path / ".codex-home")
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
    assert "riddle-codex-" in env["CODEX_HOME"]
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


def test_generate_riddle_uses_ephemeral_home(tmp_path):
    """generate_riddle() creates a fresh temp dir for CODEX_HOME and removes it after."""
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

    codex_home_used = None

    def capture_run(cmd, **kwargs):
        nonlocal codex_home_used
        env = kwargs.get("env", {})
        codex_home_used = env.get("CODEX_HOME")
        return _mock_run(output)

    svc = RiddleService(codex_home=tmp_path / ".codex-home")

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    with patch("riddle.service.subprocess.run", side_effect=capture_run), \
         patch("riddle.service._OUTPUT_FILE", output_file), \
         patch("riddle.service.subprocess.Popen", return_value=mock_proc), \
         patch("riddle.service.urllib.request.urlopen"):
        svc.generate_riddle()

    # The CODEX_HOME should have been a temp dir, not the fixed ~/.riddle-codex
    assert codex_home_used is not None, "CODEX_HOME was not set in env"
    assert "/tmp" in codex_home_used or "tmp" in codex_home_used.lower(), \
        f"CODEX_HOME should be a temp dir, got: {codex_home_used}"
    assert str(Path.home() / ".riddle-codex") not in codex_home_used, \
        "CODEX_HOME should not be the fixed ~/.riddle-codex path"
    # After generate_riddle returns, the ephemeral dir must be cleaned up
    assert not Path(codex_home_used).exists(), \
        f"Ephemeral CODEX_HOME should be removed after execution, but {codex_home_used} still exists"


def test_ephemeral_home_contains_sync_items(tmp_path):
    """Ephemeral dir has AGENTS.md, .codex/, auth.json but NO sessions/ or tmp/."""
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

    # Create source files that should be synced into ephemeral home
    source_home = tmp_path / ".codex-home"
    source_home.mkdir()
    (source_home / "AGENTS.md").write_text("# Agents")
    (source_home / ".codex").mkdir()
    (source_home / ".codex" / "config.toml").write_text("[settings]")
    (source_home / "auth.json").write_text("{}")

    ephemeral_contents: dict[str, bool] = {}

    def capture_run(cmd, **kwargs):
        env = kwargs.get("env", {})
        codex_home = env.get("CODEX_HOME", "")
        if codex_home:
            p = Path(codex_home)
            ephemeral_contents["AGENTS.md"] = (p / "AGENTS.md").exists()
            ephemeral_contents[".codex"] = (p / ".codex").is_dir()
            ephemeral_contents["auth.json"] = (p / "auth.json").exists()
            ephemeral_contents["sessions_absent"] = not (p / "sessions").exists()
            ephemeral_contents["tmp_absent"] = not (p / "tmp").exists()
        return _mock_run(output)

    svc = RiddleService(codex_home=source_home)

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    with patch("riddle.service.subprocess.run", side_effect=capture_run), \
         patch("riddle.service._OUTPUT_FILE", output_file), \
         patch("riddle.service.subprocess.Popen", return_value=mock_proc), \
         patch("riddle.service.urllib.request.urlopen"):
        svc.generate_riddle()

    assert ephemeral_contents.get("AGENTS.md"), "AGENTS.md should exist in ephemeral home"
    assert ephemeral_contents.get(".codex"), ".codex/ should exist in ephemeral home"
    assert ephemeral_contents.get("auth.json"), "auth.json should exist in ephemeral home"
    assert ephemeral_contents.get("sessions_absent"), "sessions/ should NOT exist in ephemeral home"
    assert ephemeral_contents.get("tmp_absent"), "tmp/ should NOT exist in ephemeral home"
