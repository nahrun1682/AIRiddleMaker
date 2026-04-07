# Scorer MCP Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 採点エージェント（scorer）を FastAPI + fastapi_mcp 経由の MCP サーバーに変換し、codex がネイティブ MCP ツールとして呼び出せるようにする

**Architecture:** scorer_server.py は FastAPI アプリで `/score` POST エンドポイント + Swagger UI を提供。fastapi_mcp がそのエンドポイントを MCP ツールとして `/mcp` に公開。service.py が codex exec の前後でサーバーのライフサイクルを管理。codex は `.codex/config.toml` の `[mcp_servers.scorer]` 経由で Streamable HTTP 接続。

**Tech Stack:** Python 3.12, FastAPI, fastapi_mcp, openai SDK, uvicorn, pydantic

---

### Task 1: Install dependencies

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add dependencies to pyproject.toml**

```toml
dependencies = [
    "pydantic>=2.0",
    "fastapi>=0.115",
    "fastapi-mcp>=0.4.0",
    "openai>=1.60",
    "uvicorn>=0.34",
]
```

**Step 2: Install**

Run: `uv sync`
Expected: SUCCESS, all packages installed

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "deps: add fastapi, fastapi-mcp, openai, uvicorn"
```

---

### Task 2: Add `[scorer]` section to config

**Files:**
- Modify: `riddle.toml`
- Modify: `src/riddle/config.py`
- Modify: `tests/test_config.py`

**Step 1: Write the failing tests**

```python
# tests/test_config.py に追加

def test_load_riddle_config_scorer_defaults(tmp_path):
    config = load_riddle_config(tmp_path / "missing.toml")
    assert config.scorer_model == "gpt-5.4"
    assert config.scorer_port == 19120


def test_load_riddle_config_scorer_from_file(tmp_path):
    cfg = tmp_path / "riddle.toml"
    cfg.write_text(
        "\n".join([
            'model = "gpt-5.4"',
            "",
            "[scorer]",
            'model = "gpt-5.3-codex"',
            "port = 19200",
        ])
    )
    config = load_riddle_config(cfg)
    assert config.scorer_model == "gpt-5.3-codex"
    assert config.scorer_port == 19200
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL — `scorer_model` attribute missing

**Step 3: Update RiddleConfig and loader**

`src/riddle/config.py` に `scorer_model` と `scorer_port` を追加:

```python
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
```

**Step 4: Update riddle.toml with scorer section**

```toml
[scorer]
model = "gpt-5.4"
port = 19120
```

**Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_config.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add src/riddle/config.py tests/test_config.py riddle.toml
git commit -m "feat: add [scorer] section to riddle config"
```

---

### Task 3: Create scorer prompt file

**Files:**
- Create: `src/riddle/scorer_prompt.md`
- Remove: `.codex-home/.codex/agents/scorer.toml` (後の Task で削除)

**Step 1: Extract scoring prompt from scorer.toml**

`src/riddle/scorer_prompt.md` に scorer.toml の `developer_instructions` をそのまま移す。
先頭の `# 採点エージェント（厳格版）` から末尾の JSON フォーマット例まで全文コピー。
変更なし — 「答えを聞かれたらJSON のみ返す」を維持。

**Step 2: Commit**

```bash
git add src/riddle/scorer_prompt.md
git commit -m "feat: extract scorer prompt to standalone markdown"
```

---

### Task 4: Create scorer_server.py

**Files:**
- Create: `src/riddle/scorer_server.py`
- Create: `tests/test_scorer_server.py`

**Step 1: Write the failing tests**

```python
# tests/test_scorer_server.py
import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with mocked OpenAI."""
    from riddle.scorer_server import create_app
    app = create_app(model="gpt-5.4", api_key="test-key")
    return TestClient(app)


def _mock_openai_response(content: dict) -> MagicMock:
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(content)
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


def test_score_endpoint_returns_score(client):
    score_data = {
        "uniqueness": True,
        "single_paradox": True,
        "observation_based": True,
        "strict_score": 7.5,
        "passed": True,
        "reason": "良問",
        "strict_review": "厳しく評価：7.5/10点",
    }
    with patch("riddle.scorer_server._openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_openai_response(score_data)
        resp = client.post("/score", json={"question": "q", "answer": "a"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["strict_score"] == 7.5
    assert data["passed"] is True


def test_score_endpoint_validates_input(client):
    resp = client.post("/score", json={"question": ""})
    assert resp.status_code == 422


def test_mcp_endpoint_exists(client):
    # fastapi_mcp mounts at /mcp
    resp = client.get("/mcp")
    assert resp.status_code != 404
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_scorer_server.py -v`
Expected: FAIL — module not found

**Step 3: Implement scorer_server.py**

```python
# src/riddle/scorer_server.py
"""Scorer MCP server — FastAPI + fastapi_mcp で採点ツールを MCP 公開する."""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from openai import OpenAI
from pydantic import BaseModel, Field

_PROMPT_PATH = Path(__file__).parent / "scorer_prompt.md"
_openai_client: OpenAI | None = None
_scorer_model: str = "gpt-5.4"


class ScoreRequest(BaseModel):
    question: str = Field(..., min_length=1, description="なぞなぞ問題文")
    answer: str = Field(..., min_length=1, description="なぞなぞの答え")


class ScoreResponse(BaseModel):
    uniqueness: bool
    single_paradox: bool
    observation_based: bool
    strict_score: float = Field(ge=0.0, le=10.0)
    passed: bool
    reason: str | None = None
    strict_review: str | None = None


def _load_system_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def create_app(model: str = "gpt-5.4", api_key: str | None = None) -> FastAPI:
    global _openai_client, _scorer_model
    _scorer_model = model

    if api_key:
        _openai_client = OpenAI(api_key=api_key)
    else:
        _openai_client = OpenAI()  # OPENAI_API_KEY env var

    app = FastAPI(
        title="Riddle Scorer",
        description="日本語なぞなぞ採点 MCP サーバー",
    )

    @app.post("/score", response_model=ScoreResponse)
    def score_riddle(req: ScoreRequest) -> ScoreResponse:
        """なぞなぞを採点し、スコアと合否を返す。"""
        system_prompt = _load_system_prompt()
        user_prompt = f"問題文: {req.question}\n答え: {req.answer}"

        response = _openai_client.chat.completions.create(
            model=_scorer_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)
        return ScoreResponse(**data)

    mcp = FastApiMCP(app)
    mcp.mount()

    return app


def main() -> None:
    import argparse
    import os
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from riddle.config import load_riddle_config

    parser = argparse.ArgumentParser(description="Scorer MCP Server")
    parser.add_argument("--port", type=int, help="ポート番号")
    parser.add_argument("--model", type=str, help="採点モデル")
    args = parser.parse_args()

    config_path = Path(os.getenv("RIDDLE_CONFIG_FILE", "riddle.toml"))
    config = load_riddle_config(config_path)

    port = args.port or config.scorer_port
    model = args.model or config.scorer_model

    dotenv_path = Path(__file__).parent.parent.parent / ".env"
    if dotenv_path.is_file():
        for line in dotenv_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

    import uvicorn
    app = create_app(model=model)
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_scorer_server.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add src/riddle/scorer_server.py tests/test_scorer_server.py
git commit -m "feat: add scorer MCP server with FastAPI + fastapi_mcp"
```

---

### Task 5: Update codex config for MCP

**Files:**
- Modify: `.codex-home/.codex/config.toml`
- Remove: `.codex-home/.codex/agents/scorer.toml`
- Modify: `tests/test_subagent_config.py`

**Step 1: Write failing tests**

`tests/test_subagent_config.py` を置き換え:

```python
import tomllib
from pathlib import Path


def test_codex_config_has_mcp_scorer():
    config_path = Path(".codex-home/.codex/config.toml")
    assert config_path.exists()

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert "mcp_servers" in data
    assert "scorer" in data["mcp_servers"]
    scorer = data["mcp_servers"]["scorer"]
    assert "url" in scorer
    assert "/mcp" in scorer["url"]


def test_scorer_subagent_toml_removed():
    """scorer.toml should no longer exist — scorer is now an MCP server."""
    assert not Path(".codex-home/.codex/agents/scorer.toml").exists()


def test_codex_config_no_multi_agent():
    """multi_agent feature is no longer needed."""
    config_path = Path(".codex-home/.codex/config.toml")
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    features = data.get("features", {})
    assert features.get("multi_agent") is not True
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_subagent_config.py -v`
Expected: FAIL — scorer.toml still exists, no mcp_servers section

**Step 3: Update config.toml**

`.codex-home/.codex/config.toml`:

```toml
model = "gpt-5.3-codex"
model_reasoning_effort = "medium"
web_search = "live"

[mcp_servers.scorer]
url = "http://localhost:19120/mcp"
```

**Step 4: Remove scorer.toml**

```bash
rm .codex-home/.codex/agents/scorer.toml
```

agents ディレクトリが空になったら:

```bash
rmdir .codex-home/.codex/agents 2>/dev/null || true
```

**Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_subagent_config.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add .codex-home/.codex/config.toml tests/test_subagent_config.py
git rm .codex-home/.codex/agents/scorer.toml
git commit -m "feat: replace scorer subagent with MCP server config"
```

---

### Task 6: Update AGENTS.md

**Files:**
- Modify: `.codex-home/AGENTS.md`

**Step 1: Update scorer references**

AGENTS.md の変更箇所：

1. 「重要ルール」セクション:
   - Before: `サブエージェント \`scorer\` は **必ず** 呼び出すこと（自分で採点しない）`
   - After: `MCP ツール \`score_riddle\` を **必ず** 呼び出すこと（自分で採点しない）`

2. Step 3 タイトル:
   - Before: `### Step 3: scorer で採点`
   - After: `### Step 3: score_riddle ツールで採点`

3. Step 3 本文:
   - Before: `サブエージェント \`scorer\` に問題文と答えを渡し、採点結果のJSONを受け取る。`
   - After: `MCP ツール \`score_riddle\` を呼び出し、question と answer を渡す。採点結果のJSONが返る。`

4. scorer サブエージェント依存テキストをすべて `score_riddle ツール` に変更

**Step 2: Run existing tests**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS (AGENTS.md はテスト対象外だが他のテストが壊れないことを確認)

**Step 3: Commit**

```bash
git add .codex-home/AGENTS.md
git commit -m "feat: update AGENTS.md to use score_riddle MCP tool"
```

---

### Task 7: Update service.py — scorer server lifecycle

**Files:**
- Modify: `src/riddle/service.py`
- Modify: `tests/test_service.py`

**Step 1: Write failing tests**

```python
# tests/test_service.py に追加

def test_generate_riddle_starts_scorer_server(service, tmp_path):
    """service.py が scorer server を起動・停止すること."""
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

    with patch("riddle.service.subprocess.run", return_value=_mock_run(output)) as mock_run, \
         patch("riddle.service._OUTPUT_FILE", output_file), \
         patch("riddle.service.subprocess.Popen") as mock_popen, \
         patch("riddle.service.urllib.request.urlopen"):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc

        service.generate_riddle(scorer_port=19120, scorer_model="gpt-5.4")

    # scorer server was started
    mock_popen.assert_called_once()
    popen_args = mock_popen.call_args[0][0]
    assert "scorer_server" in " ".join(popen_args)

    # scorer server was terminated
    mock_proc.terminate.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_service.py::test_generate_riddle_starts_scorer_server -v`
Expected: FAIL — scorer_port parameter not accepted

**Step 3: Update service.py**

`generate_riddle()` に `scorer_port` と `scorer_model` パラメータ追加。
メソッド内でスコアラーサーバーの起動・待機・停止を行う:

```python
import urllib.request
import urllib.error

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
    # Wait for server to be ready (max 10 seconds)
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
```

generate_riddle() の冒頭で `_start_scorer_server()` を呼び、finally で `proc.terminate()` する。

**Step 4: Update prompt text**

`generate_riddle()` の prompt から「サブエージェント `scorer`」を削除。
代わりに「score_riddle ツールを使って採点」のような指示文に変更。

既存テスト `test_generate_riddle_includes_scorer_subagent_instruction` も更新:

```python
def test_generate_riddle_includes_scorer_tool_instruction(service, tmp_path):
    # ... same setup ...
    prompt = mock_run.call_args[0][0][-1]
    assert "score_riddle" in prompt
```

**Step 5: Run all tests**

Run: `uv run pytest tests/test_service.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add src/riddle/service.py tests/test_service.py
git commit -m "feat: manage scorer server lifecycle in service.py"
```

---

### Task 8: Update main.py to pass scorer config

**Files:**
- Modify: `src/riddle/main.py`

**Step 1: Pass scorer_port and scorer_model from config**

```python
result = service.generate_riddle(
    ...
    scorer_port=config.scorer_port,
    scorer_model=config.scorer_model,
)
```

**Step 2: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add src/riddle/main.py
git commit -m "feat: pass scorer config from riddle.toml to service"
```

---

### Task 9: Clean up stale items and sync

**Files:**
- Modify: `src/riddle/service.py`

**Step 1: Update _SYNC_ITEMS and _STALE_ITEMS**

`_STALE_ITEMS` に `"agents"` フォルダを残す（旧構造クリーンアップ用）。
`_SYNC_ITEMS` はそのまま `["AGENTS.md", ".codex", "auth.json"]`。
`.codex/agents/` ディレクトリが削除済みなのでシンク時にも不要。

**Step 2: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS

**Step 3: Commit (if changes)**

```bash
git add src/riddle/service.py
git commit -m "chore: update stale items cleanup list"
```

---

### Task 10: Full test suite

**Step 1: Run full test suite**

Run: `uv run pytest tests/ -v --tb=short`
Expected: ALL PASS

**Step 2: Manual smoke test (optional)**

```bash
# scorer server 単体起動テスト
uv run python -m riddle.scorer_server &
sleep 2
curl -X POST http://localhost:19120/score \
  -H "Content-Type: application/json" \
  -d '{"question": "食べるほど減るのに食べないと増えるものは？", "answer": "食欲"}'
# → JSON score response
# Swagger UI: http://localhost:19120/docs
kill %1
```

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: scorer MCP server complete — FastAPI + fastapi_mcp"
```
