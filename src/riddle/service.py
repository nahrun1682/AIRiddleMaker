import json
import os
import subprocess
from pathlib import Path

from riddle.models import RiddleResult

_OUTPUT_FILE = Path("/tmp/riddle_output.txt")


class RiddleService:
    def __init__(self, codex_home: Path | None = None):
        self.codex_home = codex_home or Path(__file__).parent.parent.parent / ".codex-home"

    def generate_riddle(self, pattern: str | None = None) -> RiddleResult:
        prompt = "なぞなぞを1問生成してください。"
        if pattern:
            prompt += f"パターン: {pattern}"

        env = {**os.environ, "CODEX_HOME": str(self.codex_home)}

        subprocess.run(
            [
                "codex", "exec",
                "--dangerously-bypass-approvals-and-sandbox",
                "-o", str(_OUTPUT_FILE),
                prompt,
            ],
            env=env,
            capture_output=True,
            text=True,
        )

        raw = Path(_OUTPUT_FILE).read_text()
        data = json.loads(raw)

        if "error" in data:
            raise RuntimeError(data["error"])

        return RiddleResult.model_validate(data)
