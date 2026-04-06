from pathlib import Path

from riddle.config import RiddleConfig, load_riddle_config


def test_load_riddle_config_defaults_when_file_missing(tmp_path):
    config = load_riddle_config(tmp_path / "missing.toml")
    assert isinstance(config, RiddleConfig)
    assert config.model == "gpt-5.3-codex"
    assert config.reasoning_effort == "medium"
    assert config.max_retries == 10
    assert config.strict_threshold == 9.5
    assert config.require_reason_fields is True
    assert config.trace_default is False


def test_load_riddle_config_from_file(tmp_path):
    cfg = tmp_path / "riddle.toml"
    cfg.write_text(
        "\n".join(
            [
                'model = "gpt-5.4"',
                'reasoning_effort = "high"',
                "max_retries = 12",
                "strict_threshold = 9.7",
                "require_reason_fields = false",
                "trace_default = true",
            ]
        )
    )
    config = load_riddle_config(cfg)
    assert config.model == "gpt-5.4"
    assert config.reasoning_effort == "high"
    assert config.max_retries == 12
    assert config.strict_threshold == 9.7
    assert config.require_reason_fields is False
    assert config.trace_default is True
