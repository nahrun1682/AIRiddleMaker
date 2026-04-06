import tomllib
from pathlib import Path


def test_scorer_subagent_toml_exists_and_has_required_fields():
    config_path = Path(".codex-home/agents/scorer.toml")
    assert config_path.exists()

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert data["name"] == "scorer"
    assert isinstance(data["description"], str) and data["description"]
    assert isinstance(data["model"], str) and data["model"]
    assert isinstance(data["color"], str) and data["color"]
    assert isinstance(data["developer_instructions"], str)
    assert "strict_score" in data["developer_instructions"]
