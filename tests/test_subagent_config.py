import tomllib
from pathlib import Path


def test_scorer_subagent_toml_exists_and_has_required_fields():
    config_path = Path(".codex-home/.codex/agents/scorer.toml")
    assert config_path.exists()

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert data["name"] == "scorer"
    assert isinstance(data["description"], str) and data["description"]
    assert isinstance(data["model"], str) and data["model"]
    assert isinstance(data["developer_instructions"], str)
    assert "strict_score" in data["developer_instructions"]


def test_codex_project_config_exists():
    config_path = Path(".codex-home/.codex/config.toml")
    assert config_path.exists()

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert data.get("features", {}).get("multi_agent") is True
    assert "agents" in data
