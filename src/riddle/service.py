import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from riddle.log_stream import SessionTailer, format_event
from riddle.models import RiddleResult

_SYNC_ITEMS = ["AGENTS.md", ".codex", "auth.json"]


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


class CodexHomeManager:
    def __init__(self, source_home: Path, sync_items: list[str] | None = None):
        self._source_home = source_home
        self._sync_items = sync_items or _SYNC_ITEMS

    def create(self) -> Path:
        """Create a disposable CODEX_HOME with only config files, no history."""
        ephemeral = Path(tempfile.mkdtemp(prefix="riddle-codex-"))
        for item in self._sync_items:
            src = self._source_home / item
            dst = ephemeral / item
            if not src.exists():
                continue
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        return ephemeral

    def cleanup(self, path: Path) -> None:
        shutil.rmtree(path, ignore_errors=True)


class ScorerProcessManager:
    def __init__(self):
        self._scorer_log: tempfile._TemporaryFileWrapper[str] | None = None

    def start(self, port: int, model: str, env: dict[str, str]) -> subprocess.Popen:
        """Start scorer MCP server as background process."""
        self._scorer_log = tempfile.NamedTemporaryFile(
            prefix="riddle-scorer-",
            suffix=".log",
            delete=False,
            mode="w",
        )
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "riddle.scorer_server",
                "--port",
                str(port),
                "--model",
                model,
            ],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=self._scorer_log,
        )

        url = f"http://localhost:{port}/docs"
        for _ in range(50):
            try:
                urllib.request.urlopen(url, timeout=1)
                return proc
            except (urllib.error.URLError, ConnectionError):
                time.sleep(0.2)
                if proc.poll() is not None:
                    self._scorer_log.flush()
                    stderr = Path(self._scorer_log.name).read_text()
                    self.stop(proc)
                    raise RuntimeError(f"Scorer server failed to start: {stderr}")

        self.stop(proc)
        raise RuntimeError("Scorer server startup timed out")

    def stop(self, proc: subprocess.Popen) -> None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)

        if self._scorer_log is not None:
            self._scorer_log.close()
            try:
                os.unlink(self._scorer_log.name)
            except OSError:
                pass
            self._scorer_log = None


class CodexExecRunner:
    def run(
        self,
        *,
        ephemeral_home: Path,
        model: str,
        reasoning_effort: str,
        scorer_port: int,
        output_path: Path,
        prompt: str,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "codex",
                "exec",
                "-C",
                str(ephemeral_home),
                "-m",
                model,
                "-c",
                f'model_reasoning_effort="{reasoning_effort}"',
                "-c",
                f'mcp_servers.scorer.url="http://localhost:{scorer_port}/mcp"',
                "--dangerously-bypass-approvals-and-sandbox",
                "-o",
                str(output_path),
                prompt,
            ],
            env=env,
            capture_output=True,
            text=True,
        )


class RiddleOutputParser:
    def parse(
        self,
        *,
        output_path: Path,
        strict_threshold: float,
        require_reason_fields: bool,
    ) -> RiddleResult:
        if not output_path.exists():
            raise RuntimeError("codex exec did not produce an output file")

        raw = output_path.read_text().strip()
        if not raw:
            raise RuntimeError("codex exec produced an empty output file")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"codex output is not valid JSON: {e}\\nraw output: {raw[:500]}"
            ) from e

        if "error" in data:
            raise RuntimeError(data["error"])

        result = RiddleResult.model_validate(data)
        if result.score.passed != result.score.expected_pass(strict_threshold):
            raise RuntimeError("strict_threshold validation failed")

        if require_reason_fields and (not result.score.reason or not result.score.strict_review):
            raise RuntimeError("reason/strict_review is required")

        return result


class RiddleService:
    def __init__(
        self,
        codex_home: Path | None = None,
        home_manager: CodexHomeManager | None = None,
        scorer_manager: ScorerProcessManager | None = None,
        codex_runner: CodexExecRunner | None = None,
        output_parser: RiddleOutputParser | None = None,
    ):
        source_home = codex_home or Path(__file__).parent.parent.parent / ".codex-home"
        self._dotenv_path = Path(__file__).parent.parent.parent / ".env"
        self._home_manager = home_manager or CodexHomeManager(source_home)
        self._scorer_manager = scorer_manager or ScorerProcessManager()
        self._codex_runner = codex_runner or CodexExecRunner()
        self._output_parser = output_parser or RiddleOutputParser()

    def _create_output_path(self) -> Path:
        with tempfile.NamedTemporaryFile(
            prefix="riddle-output-",
            suffix=".json",
            delete=False,
        ) as output_file:
            return Path(output_file.name)

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
            prompt += f"パターン: {pattern} に固定。他のパターンに切り替えてはいけません。"
        prompt += (
            f"最大{max_retries}回まで試行し、"
            "採点は MCP ツール score_riddle を使って実施し、"
            f"strict_score は {strict_threshold} 以上を合格基準とし、"
            "strict_score / passed / reason / strict_review を含む指定JSONのみを出力してください。"
        )

        ephemeral_home = self._home_manager.create()
        output_path = self._create_output_path()
        stop_trace = threading.Event()
        trace_thread: threading.Thread | None = None
        tailer: SessionTailer | None = None

        try:
            env = {
                **os.environ,
                **_load_dotenv(self._dotenv_path),
                "CODEX_HOME": str(ephemeral_home),
            }

            if trace:
                tailer = SessionTailer(ephemeral_home, time.time())

                def _trace_loop() -> None:
                    assert tailer is not None
                    while not stop_trace.is_set():
                        for event in tailer.poll():
                            print(format_event(event), file=sys.stderr)
                        time.sleep(0.2)

                trace_thread = threading.Thread(target=_trace_loop, daemon=True)
                trace_thread.start()

            scorer_proc = self._scorer_manager.start(scorer_port, scorer_model, env)
            try:
                proc = self._codex_runner.run(
                    ephemeral_home=ephemeral_home,
                    model=model,
                    reasoning_effort=reasoning_effort,
                    scorer_port=scorer_port,
                    output_path=output_path,
                    prompt=prompt,
                    env=env,
                )
            finally:
                self._scorer_manager.stop(scorer_proc)
                if trace:
                    stop_trace.set()
                    if trace_thread is not None:
                        trace_thread.join(timeout=1.0)
                    if tailer is not None:
                        for event in tailer.poll():
                            print(format_event(event), file=sys.stderr)

            if proc.returncode != 0:
                stderr_msg = proc.stderr.strip() if proc.stderr else "unknown error"
                raise RuntimeError(
                    f"codex exec failed (exit {proc.returncode}): {stderr_msg}"
                )

            return self._output_parser.parse(
                output_path=output_path,
                strict_threshold=strict_threshold,
                require_reason_fields=require_reason_fields,
            )
        finally:
            self._home_manager.cleanup(ephemeral_home)
            try:
                output_path.unlink()
            except OSError:
                pass
