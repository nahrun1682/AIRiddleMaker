from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class RiddleConfig:
    model: str = "gpt-5.3-codex"
    reasoning_effort: str = "medium"
    max_retries: int = 10
    strict_threshold: float = 6.0
    require_reason_fields: bool = True
    trace_default: bool = False
    scorer_model: str = "gpt-5.4"
    scorer_port: int = 19120


def load_riddle_config(path: Path) -> RiddleConfig:
    if not path.exists():
        return RiddleConfig()

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    scorer = data.get("scorer", {})
    return RiddleConfig(
        model=str(data.get("model", RiddleConfig.model)),
        reasoning_effort=str(data.get("reasoning_effort", RiddleConfig.reasoning_effort)),
        max_retries=int(data.get("max_retries", RiddleConfig.max_retries)),
        strict_threshold=float(data.get("strict_threshold", RiddleConfig.strict_threshold)),
        require_reason_fields=bool(
            data.get("require_reason_fields", RiddleConfig.require_reason_fields)
        ),
        trace_default=bool(data.get("trace_default", RiddleConfig.trace_default)),
        scorer_model=str(scorer.get("model", RiddleConfig.scorer_model)),
        scorer_port=int(scorer.get("port", RiddleConfig.scorer_port)),
    )
