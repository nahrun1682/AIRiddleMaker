import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path

from riddle.log_stream import SessionTailer, format_event
from riddle.models import RiddleResult

_OUTPUT_FILE = Path("/tmp/riddle_output.txt")

_SYNC_ITEMS = ["AGENTS.md", ".codex", "auth.json"]

# Items from old flat structure that should be removed from runtime dir
_STALE_ITEMS = ["config.toml", "agents", "skills"]


def _load_dotenv(path: Path) -> dict[str, str]:
    """Read a .env file and return key=value pairs (no shell expansion)."""
    result: dict[str, str] = {}
    if not path.is_file():
        return result
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip().strip("'\"")
    return result


class RiddleService:
    def __init__(self, codex_home: Path | None = None):
        self._source_home = codex_home or Path(__file__).parent.parent.parent / ".codex-home"
        self.codex_home = Path.home() / ".riddle-codex"
        self._sync_runtime_home()

    def _sync_runtime_home(self) -> None:
        """Copy config from repo .codex-home/ to runtime dir outside project tree."""
        self.codex_home.mkdir(parents=True, exist_ok=True)
        # Remove stale items from old flat structure
        for item in _STALE_ITEMS:
            stale = self.codex_home / item
            if stale.is_dir():
                shutil.rmtree(stale)
            elif stale.exists():
                stale.unlink()
        for item in _SYNC_ITEMS:
            src = self._source_home / item
            dst = self.codex_home / item
            if not src.exists():
                continue
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

    def _start_scorer_server(self, port: int, model: str) -> subprocess.Popen:
        """Start scorer MCP server as background process."""
        env = {
            **os.environ,
            **_load_dotenv(Path(__file__).parent.parent.parent / ".env"),
        }
        proc = subprocess.Popen(
            [
                sys.executable, "-m", "riddle.scorer_server",
                "--port", str(port),
                "--model", model,
            ],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        url = f"http://localhost:{port}/docs"
        for _ in range(50):
            try:
                urllib.request.urlopen(url, timeout=1)
                return proc
            except (urllib.error.URLError, ConnectionError):
                time.sleep(0.2)
                if proc.poll() is not None:
                    stderr = proc.stderr.read().decode() if proc.stderr else ""
                    raise RuntimeError(f"Scorer server failed to start: {stderr}")
        proc.terminate()
        raise RuntimeError("Scorer server startup timed out")

    def generate_riddle(
        self,
        pattern: str | None = None,
        theme: str | None = None,
        max_retries: int = 10,
        trace: bool = False,
        model: str = "gpt-5.3-codex",
        reasoning_effort: str = "medium",
        strict_threshold: float = 6.0,
        require_reason_fields: bool = True,
        scorer_port: int = 19120,
        scorer_model: str = "gpt-5.4",
    ) -> RiddleResult:
        if max_retries < 1:
            raise ValueError("max_retries must be >= 1")

        prompt = "なぞなぞを1問生成してください。"
        if theme:
            prompt += f"テーマ: {theme}。"
        if pattern:
            prompt += f"パターン: {pattern}"
        prompt += (
            f"。最大{max_retries}回まで試行し、"
            "採点は MCP ツール score_riddle を使って実施し、"
            f"strict_score は {strict_threshold} 以上を合格基準とし、"
            "strict_score / passed / reason / strict_review を含む指定JSONのみを出力してください。"
        )

        env = {
            **os.environ,
            **_load_dotenv(Path(__file__).parent.parent.parent / ".env"),
            "CODEX_HOME": str(self.codex_home),
        }

        stop_trace = threading.Event()
        trace_thread: threading.Thread | None = None
        tailer: SessionTailer | None = None
        if trace:
            tailer = SessionTailer(self.codex_home, time.time())

            def _trace_loop() -> None:
                assert tailer is not None
                while not stop_trace.is_set():
                    for event in tailer.poll():
                        print(format_event(event), file=sys.stderr)
                    time.sleep(0.2)

            trace_thread = threading.Thread(target=_trace_loop, daemon=True)
            trace_thread.start()

        scorer_proc = self._start_scorer_server(scorer_port, scorer_model)
        try:
            proc = subprocess.run(
                [
                    "codex", "exec",
                    "-C", str(self.codex_home),
                    "-m", model,
                    "-c", f'model_reasoning_effort="{reasoning_effort}"',
                    "-c", f'mcp_servers.scorer.url="http://localhost:{scorer_port}/mcp"',
                    "--dangerously-bypass-approvals-and-sandbox",
                    "-o", str(_OUTPUT_FILE),
                    prompt,
                ],
                env=env,
                capture_output=True,
                text=True,
            )
        finally:
            scorer_proc.terminate()
            if trace:
                stop_trace.set()
                if trace_thread is not None:
                    trace_thread.join(timeout=1.0)
                if tailer is not None:
                    for event in tailer.poll():
                        print(format_event(event), file=sys.stderr)

        if proc.returncode != 0:
            stderr_msg = proc.stderr.strip() if proc.stderr else "unknown error"
            raise RuntimeError(f"codex exec failed (exit {proc.returncode}): {stderr_msg}")

        if not _OUTPUT_FILE.exists():
            raise RuntimeError("codex exec did not produce an output file")

        raw = _OUTPUT_FILE.read_text().strip()
        if not raw:
            raise RuntimeError("codex exec produced an empty output file")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"codex output is not valid JSON: {e}\nraw output: {raw[:500]}") from e

        if "error" in data:
            raise RuntimeError(data["error"])

        result = RiddleResult.model_validate(data)
        expected_pass = (
            result.score.single_paradox
            and result.score.observation_based
            and result.score.strict_score >= strict_threshold
        )
        if result.score.passed != expected_pass:
            raise RuntimeError("strict_threshold validation failed")

        if require_reason_fields and (not result.score.reason or not result.score.strict_review):
            raise RuntimeError("reason/strict_review is required")

        return result
