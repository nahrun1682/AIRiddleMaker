import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from riddle.models import RiddleResult
from riddle.service import RiddleService


@pytest.fixture
def service(tmp_path):
    svc = RiddleService(codex_home=tmp_path / ".codex-home")
    return svc


@pytest.fixture(autouse=True)
def mock_scorer_server():
    """Default scorer server mock for generate_riddle tests."""
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    with patch("riddle.service.subprocess.Popen", return_value=mock_proc), \
         patch("riddle.service.urllib.request.urlopen"):
        yield mock_proc


def _mock_run(output: dict) -> MagicMock:
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout = json.dumps(output)
    return mock


def _codex_run_side_effect(output: dict, output_paths: list[Path] | None = None, observe=None):
    def _side_effect(cmd, **kwargs):
        if observe is not None:
            observe(cmd, kwargs)
        out_index = cmd.index("-o") + 1
        out_path = Path(cmd[out_index])
        if output_paths is not None:
            output_paths.append(out_path)
        out_path.write_text(json.dumps(output), encoding="utf-8")
        return _mock_run(output)

    return _side_effect


def test_generate_riddle_success(service):
    output = {
        "question": "食べるほど減るのに、食べないと増えるものは？",
        "answer": "食欲",
        "pattern": "paradox",
        "score": {
            "uniqueness": True,
            "structural_soundness": True,
            "concrete_grounding": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 2,
    }

    with patch("riddle.service.subprocess.run", side_effect=_codex_run_side_effect(output)) as mock_run:
        result = service.generate_riddle()

    assert isinstance(result, RiddleResult)
    assert result.answer == "食欲"
    assert result.attempts == 2
    assert mock_run.called


def test_generate_riddle_sets_codex_home(service):
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "pun",
        "score": {
            "uniqueness": True,
            "structural_soundness": True,
            "concrete_grounding": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }

    with patch("riddle.service.subprocess.run", side_effect=_codex_run_side_effect(output)) as mock_run:
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


def test_generate_riddle_includes_theme_in_prompt(service):
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "pun",
        "score": {
            "uniqueness": True,
            "structural_soundness": True,
            "concrete_grounding": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }

    with patch("riddle.service.subprocess.run", side_effect=_codex_run_side_effect(output)) as mock_run:
        service.generate_riddle(theme="食べ物")

    cmd = mock_run.call_args[0][0]
    prompt = cmd[-1]
    assert "食べ物" in prompt


def test_generate_riddle_includes_max_retries_in_prompt(service):
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "pun",
        "score": {
            "uniqueness": True,
            "structural_soundness": True,
            "concrete_grounding": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }

    with patch("riddle.service.subprocess.run", side_effect=_codex_run_side_effect(output)) as mock_run:
        service.generate_riddle(max_retries=12)

    prompt = mock_run.call_args[0][0][-1]
    assert "最大12回" in prompt


def test_generate_riddle_includes_scorer_subagent_instruction(service):
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "pun",
        "score": {
            "uniqueness": True,
            "structural_soundness": True,
            "concrete_grounding": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }

    with patch("riddle.service.subprocess.run", side_effect=_codex_run_side_effect(output)) as mock_run:
        service.generate_riddle()

    prompt = mock_run.call_args[0][0][-1]
    assert "score_riddle" in prompt


def test_generate_riddle_passes_mcp_config_via_cli(service):
    """codex exec must receive -c flag configuring the scorer MCP server."""
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "pun",
        "score": {
            "uniqueness": True,
            "structural_soundness": True,
            "concrete_grounding": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }

    with patch("riddle.service.subprocess.run", side_effect=_codex_run_side_effect(output)) as mock_run:
        service.generate_riddle(scorer_port=19120, scorer_model="gpt-5.4")

    cmd = mock_run.call_args[0][0]
    c_values = []
    for i, arg in enumerate(cmd):
        if arg == "-c" and i + 1 < len(cmd):
            c_values.append(cmd[i + 1])

    mcp_config = [v for v in c_values if "mcp_servers" in v and "19120" in v]
    assert mcp_config, f"No MCP server config in -c flags: {c_values}"


def test_generate_riddle_starts_and_stops_scorer(service):
    """service starts scorer server before codex exec and stops it after."""
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "paradox",
        "score": {
            "uniqueness": True,
            "structural_soundness": True,
            "concrete_grounding": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    with patch("riddle.service.subprocess.run", side_effect=_codex_run_side_effect(output)), \
         patch("riddle.service.subprocess.Popen", return_value=mock_proc) as mock_popen, \
         patch("riddle.service.urllib.request.urlopen"):
        service.generate_riddle(scorer_port=19120, scorer_model="gpt-5.4")

    mock_popen.assert_called_once()
    popen_cmd = mock_popen.call_args[0][0]
    assert "scorer_server" in " ".join(str(x) for x in popen_cmd)
    mock_proc.terminate.assert_called_once()


def test_start_cleans_up_scorer_log_when_process_exits_early(tmp_path):
    from riddle.service import ScorerProcessManager

    log_files = []
    original_named_tempfile = tempfile.NamedTemporaryFile

    def named_tempfile_spy(*args, **kwargs):
        handle = original_named_tempfile(*args, **kwargs)
        log_files.append(handle)
        return handle

    mock_proc = MagicMock()
    mock_proc.poll.return_value = 1

    manager = ScorerProcessManager()
    with patch("riddle.service.tempfile.NamedTemporaryFile", side_effect=named_tempfile_spy), \
         patch("riddle.service.subprocess.Popen", return_value=mock_proc), \
         patch("riddle.service.urllib.request.urlopen", side_effect=ConnectionError("down")):
        with pytest.raises(RuntimeError, match="Scorer server failed to start"):
            manager.start(port=19120, model="gpt-5.4", env={"CODEX_HOME": str(tmp_path)})

    assert log_files, "expected scorer log tempfile to be created"
    assert log_files[0].closed
    assert not Path(log_files[0].name).exists()
    mock_proc.terminate.assert_called_once()


def test_generate_riddle_validates_strict_threshold(service):
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "pun",
        "score": {
            "uniqueness": True,
            "structural_soundness": True,
            "concrete_grounding": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    with patch("riddle.service.subprocess.run", side_effect=_codex_run_side_effect(output)), \
         patch("riddle.service.subprocess.Popen", return_value=mock_proc), \
         patch("riddle.service.urllib.request.urlopen"):
        with pytest.raises(RuntimeError, match="strict_threshold"):
            service.generate_riddle(strict_threshold=9.7)


def test_generate_riddle_requires_reason_fields_when_enabled(service):
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "pun",
        "score": {
            "uniqueness": True,
            "structural_soundness": True,
            "concrete_grounding": True,
            "strict_score": 9.6,
            "passed": True,
        },
        "attempts": 1,
    }

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    with patch("riddle.service.subprocess.run", side_effect=_codex_run_side_effect(output)), \
         patch("riddle.service.subprocess.Popen", return_value=mock_proc), \
         patch("riddle.service.urllib.request.urlopen"):
        with pytest.raises(RuntimeError, match="reason/strict_review"):
            service.generate_riddle(require_reason_fields=True)


def test_generate_riddle_max_retries(service):
    output = {"error": "max_retries_exceeded", "attempts": 5}

    with patch("riddle.service.subprocess.run", side_effect=_codex_run_side_effect(output)):
        with pytest.raises(RuntimeError, match="max_retries_exceeded"):
            service.generate_riddle()


def test_generate_riddle_uses_unique_temp_output_file(service):
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "pun",
        "score": {
            "uniqueness": True,
            "structural_soundness": True,
            "concrete_grounding": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }
    observed_paths: list[Path] = []

    with patch("riddle.service.subprocess.run", side_effect=_codex_run_side_effect(output, observed_paths)):
        service.generate_riddle()
        service.generate_riddle()

    assert len(observed_paths) == 2
    assert observed_paths[0].name.startswith("riddle-output-")
    assert observed_paths[1].name.startswith("riddle-output-")
    assert observed_paths[0] != observed_paths[1]


def test_generate_riddle_removes_temp_output_file_after_parse(service):
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "pun",
        "score": {
            "uniqueness": True,
            "structural_soundness": True,
            "concrete_grounding": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }
    observed_paths: list[Path] = []

    with patch("riddle.service.subprocess.run", side_effect=_codex_run_side_effect(output, observed_paths)):
        service.generate_riddle()

    assert observed_paths, "expected codex output path to be captured"
    assert not observed_paths[0].exists()


def test_generate_riddle_uses_ephemeral_home(tmp_path):
    """generate_riddle() creates a fresh temp dir for CODEX_HOME and removes it after."""
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "pun",
        "score": {
            "uniqueness": True,
            "structural_soundness": True,
            "concrete_grounding": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }

    source_home = tmp_path / ".codex-home"
    source_home.mkdir()
    (source_home / "AGENTS.md").write_text("# Agents")
    (source_home / ".codex").mkdir()
    (source_home / ".codex" / "config.toml").write_text("[settings]")
    (source_home / "auth.json").write_text("{}")

    codex_home_used = None

    def observe(cmd, kwargs):
        nonlocal codex_home_used
        codex_home_used = (kwargs.get("env") or {}).get("CODEX_HOME")

    svc = RiddleService(codex_home=source_home)

    with patch("riddle.service.subprocess.run", side_effect=_codex_run_side_effect(output, observe=observe)):
        svc.generate_riddle()

    assert codex_home_used is not None, "CODEX_HOME was not set in env"
    assert "/tmp" in codex_home_used or "tmp" in codex_home_used.lower(), (
        f"CODEX_HOME should be a temp dir, got: {codex_home_used}"
    )
    assert str(Path.home() / ".riddle-codex") not in codex_home_used, (
        "CODEX_HOME should not be the fixed ~/.riddle-codex path"
    )
    assert not Path(codex_home_used).exists(), (
        f"Ephemeral CODEX_HOME should be removed after execution, but {codex_home_used} still exists"
    )


def test_ephemeral_home_contains_sync_items(tmp_path):
    """Ephemeral dir has AGENTS.md, .codex/, auth.json but NO sessions/ or tmp/."""
    output = {
        "question": "q",
        "answer": "a",
        "pattern": "pun",
        "score": {
            "uniqueness": True,
            "structural_soundness": True,
            "concrete_grounding": True,
            "strict_score": 9.6,
            "passed": True,
            "reason": "r",
            "strict_review": "s",
        },
        "attempts": 1,
    }

    source_home = tmp_path / ".codex-home"
    source_home.mkdir()
    (source_home / "AGENTS.md").write_text("# Agents")
    (source_home / ".codex").mkdir()
    (source_home / ".codex" / "config.toml").write_text("[settings]")
    (source_home / "auth.json").write_text("{}")

    ephemeral_contents: dict[str, bool] = {}

    def observe(cmd, kwargs):
        env = kwargs.get("env", {})
        codex_home = env.get("CODEX_HOME", "")
        if codex_home:
            p = Path(codex_home)
            ephemeral_contents["AGENTS.md"] = (p / "AGENTS.md").exists()
            ephemeral_contents[".codex"] = (p / ".codex").is_dir()
            ephemeral_contents["auth.json"] = (p / "auth.json").exists()
            ephemeral_contents["sessions_absent"] = not (p / "sessions").exists()
            ephemeral_contents["tmp_absent"] = not (p / "tmp").exists()

    svc = RiddleService(codex_home=source_home)

    with patch("riddle.service.subprocess.run", side_effect=_codex_run_side_effect(output, observe=observe)):
        svc.generate_riddle()

    assert ephemeral_contents.get("AGENTS.md"), "AGENTS.md should exist in ephemeral home"
    assert ephemeral_contents.get(".codex"), ".codex/ should exist in ephemeral home"
    assert ephemeral_contents.get("auth.json"), "auth.json should exist in ephemeral home"
    assert ephemeral_contents.get("sessions_absent"), "sessions/ should NOT exist in ephemeral home"
    assert ephemeral_contents.get("tmp_absent"), "tmp/ should NOT exist in ephemeral home"
