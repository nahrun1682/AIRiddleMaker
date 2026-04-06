import tomllib
from pathlib import Path


def test_scorer_subagent_toml_removed():
    """scorer.toml should no longer exist — scorer is now an MCP server."""
    assert not Path(".codex-home/.codex/agents/scorer.toml").exists()


def test_codex_config_has_mcp_scorer():
    config_path = Path(".codex-home/.codex/config.toml")
    assert config_path.exists()

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert "mcp_servers" in data
    scorer = data["mcp_servers"]["scorer"]
    assert "url" in scorer
    assert "19120" in scorer["url"]
    assert "/mcp" in scorer["url"]
