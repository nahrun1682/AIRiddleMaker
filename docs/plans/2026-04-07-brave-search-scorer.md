# Brave Search スコアラー統合 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** スコアラーが Brave Search API で「{answer} なぞなぞ」を検索し、検索結果に基づいてオリジナリティを判定するようにする

**Architecture:** scorer_server.py の `/score` エンドポイント内で、LLM 採点前に Brave Web Search API を GET で叩く。ヒット数＋上位スニペットをスコアラーLLM のプロンプトに注入し、「LLMの直感」ではなく「検索エビデンス」でオリジナリティを判定させる。

**Tech Stack:** Python 3.12, requests, Brave Search API (`https://api.search.brave.com/res/v1/web/search`), FastAPI, OpenAI SDK

---

### Task 1: `requests` を依存に追加

**Files:**
- Modify: `pyproject.toml:14` (`dependencies` 配列)

**Step 1: pyproject.toml に requests を追加**

`dependencies` 配列に `"requests>=2.31"` を追加する。

```toml
dependencies = [
    "pydantic>=2.0",
    "fastapi>=0.115",
    "fastapi-mcp>=0.4.0",
    "openai>=1.60",
    "uvicorn>=0.34",
    "requests>=2.31",
]
```

**Step 2: 依存を同期**

Run: `uv sync`
Expected: 成功。requests がインストールされる。

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "deps: add requests for Brave Search API"
```

---

### Task 2: Brave 検索ヘルパー関数を書く（TDD）

**Files:**
- Create: `src/riddle/brave_search.py`
- Test: `tests/test_brave_search.py`

**Step 1: テストファイルを作成**

```python
"""Tests for brave_search module."""

import json
from unittest.mock import patch, MagicMock

import pytest

from riddle.brave_search import search_riddle_evidence


BRAVE_RESPONSE_HIT = {
    "query": {"original": "春雨 なぞなぞ"},
    "web": {
        "totalEstimatedMatches": 1234,
        "results": [
            {
                "title": "春雨のなぞなぞ - なぞなぞランド",
                "url": "https://example.com/nazonazo/harusame",
                "description": "Q: 空から降ってくるのにすするものは？ A: 春雨",
            },
            {
                "title": "食べ物なぞなぞ集",
                "url": "https://example.com/food",
                "description": "春雨に関する問題が多数あります。",
            },
        ],
    },
}

BRAVE_RESPONSE_NO_HIT = {
    "query": {"original": "ガスメーター なぞなぞ"},
    "web": {
        "totalEstimatedMatches": 0,
        "results": [],
    },
}

BRAVE_RESPONSE_NO_WEB = {
    "query": {"original": "テスト なぞなぞ"},
}


def _mock_get(json_data: dict, status_code: int = 200) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    mock_resp.raise_for_status.return_value = None
    if status_code >= 400:
        mock_resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return mock_resp


class TestSearchRiddleEvidence:
    @patch("riddle.brave_search.requests.get")
    def test_returns_hit_count_and_snippets(self, mock_get):
        mock_get.return_value = _mock_get(BRAVE_RESPONSE_HIT)
        result = search_riddle_evidence("春雨", api_key="test-key")

        assert result["hit_count"] == 1234
        assert len(result["snippets"]) == 2
        assert "春雨のなぞなぞ" in result["snippets"][0]
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["params"]["q"] == "春雨 なぞなぞ"

    @patch("riddle.brave_search.requests.get")
    def test_no_hits_returns_zero(self, mock_get):
        mock_get.return_value = _mock_get(BRAVE_RESPONSE_NO_HIT)
        result = search_riddle_evidence("ガスメーター", api_key="test-key")

        assert result["hit_count"] == 0
        assert result["snippets"] == []

    @patch("riddle.brave_search.requests.get")
    def test_no_web_key_returns_zero(self, mock_get):
        mock_get.return_value = _mock_get(BRAVE_RESPONSE_NO_WEB)
        result = search_riddle_evidence("テスト", api_key="test-key")

        assert result["hit_count"] == 0
        assert result["snippets"] == []

    @patch("riddle.brave_search.requests.get")
    def test_api_error_returns_none(self, mock_get):
        mock_get.return_value = _mock_get({}, status_code=500)
        result = search_riddle_evidence("春雨", api_key="test-key")

        assert result is None

    @patch("riddle.brave_search.requests.get")
    def test_network_error_returns_none(self, mock_get):
        mock_get.side_effect = ConnectionError("timeout")
        result = search_riddle_evidence("春雨", api_key="test-key")

        assert result is None

    @patch("riddle.brave_search.requests.get")
    def test_no_api_key_returns_none(self, mock_get):
        result = search_riddle_evidence("春雨", api_key="")

        assert result is None
        mock_get.assert_not_called()
```

**Step 2: テストが失敗することを確認**

Run: `uv run pytest tests/test_brave_search.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'riddle.brave_search'`

**Step 3: 最小実装**

`src/riddle/brave_search.py`:

```python
"""Brave Search API wrapper for riddle originality evidence."""

from __future__ import annotations

import requests


def search_riddle_evidence(
    answer: str,
    api_key: str,
    max_snippets: int = 5,
    timeout: float = 5.0,
) -> dict | None:
    """Search Brave for '{answer} なぞなぞ' and return hit count + snippets.

    Returns:
        {"hit_count": int, "snippets": list[str]} on success, None on error.
    """
    if not api_key:
        return None

    query = f"{answer} なぞなぞ"

    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"X-Subscription-Token": api_key},
            params={"q": query, "count": max_snippets, "search_lang": "jp"},
            timeout=timeout,
        )
        resp.raise_for_status()
    except Exception:
        return None

    data = resp.json()
    web = data.get("web", {})
    hit_count = web.get("totalEstimatedMatches", 0)
    results = web.get("results", [])

    snippets = []
    for r in results[:max_snippets]:
        title = r.get("title", "")
        desc = r.get("description", "")
        url = r.get("url", "")
        snippets.append(f"{title} — {desc} ({url})")

    return {"hit_count": hit_count, "snippets": snippets}
```

**Step 4: テストが通ることを確認**

Run: `uv run pytest tests/test_brave_search.py -v`
Expected: 6 passed

**Step 5: Commit**

```bash
git add src/riddle/brave_search.py tests/test_brave_search.py
git commit -m "feat: add Brave Search helper for riddle originality evidence"
```

---

### Task 3: scorer_server.py に検索統合（TDD）

**Files:**
- Modify: `src/riddle/scorer_server.py`
- Modify: `tests/test_scorer_server.py`

**Step 1: 既存テストを壊さず、検索結果注入テストを追加**

`tests/test_scorer_server.py` に追加:

```python
@patch("riddle.scorer_server.search_riddle_evidence")
def test_score_injects_search_evidence_into_prompt(mock_search, client):
    """検索結果がLLMプロンプトに注入されることを確認."""
    mock_search.return_value = {
        "hit_count": 500,
        "snippets": ["春雨のなぞなぞ — Q:空から降る A:春雨 (https://example.com)"],
    }
    with patch("riddle.scorer_server._openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            PASSING_SCORE
        )
        client.post("/score", json={"question": "空から降るのにすするものは？", "answer": "春雨"})

    call_args = mock_client.chat.completions.create.call_args
    user_msg = call_args.kwargs["messages"][1]["content"]
    assert "検索ヒット数" in user_msg
    assert "500" in user_msg
    assert "春雨のなぞなぞ" in user_msg


@patch("riddle.scorer_server.search_riddle_evidence")
def test_score_works_when_search_fails(mock_search, client):
    """検索が失敗しても採点は続行する."""
    mock_search.return_value = None
    with patch("riddle.scorer_server._openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            PASSING_SCORE
        )
        resp = client.post("/score", json={"question": "q", "answer": "a"})

    assert resp.status_code == 200
    call_args = mock_client.chat.completions.create.call_args
    user_msg = call_args.kwargs["messages"][1]["content"]
    assert "検索不可" in user_msg


@patch("riddle.scorer_server.search_riddle_evidence")
def test_score_no_search_hits(mock_search, client):
    """検索0件の場合もプロンプトに反映."""
    mock_search.return_value = {"hit_count": 0, "snippets": []}
    with patch("riddle.scorer_server._openai_client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            PASSING_SCORE
        )
        client.post("/score", json={"question": "q", "answer": "a"})

    call_args = mock_client.chat.completions.create.call_args
    user_msg = call_args.kwargs["messages"][1]["content"]
    assert "検索ヒット数: 0" in user_msg
```

**Step 2: テスト失敗を確認**

Run: `uv run pytest tests/test_scorer_server.py::test_score_injects_search_evidence_into_prompt -v`
Expected: FAIL（search_riddle_evidence がまだ import されていない）

**Step 3: scorer_server.py を修正**

変更点:
1. `from riddle.brave_search import search_riddle_evidence` を追加
2. .env から `BRAVE_API_KEY` を読む
3. `score_riddle()` 内で検索してからプロンプトに注入

scorer_server.py の `score_riddle()` 関数を以下に変更:

```python
@app.post("/score", response_model=ScoreResponse, operation_id="score_riddle")
def score_riddle(req: ScoreRequest) -> ScoreResponse:
    """なぞなぞを採点し、スコアと合否を返す。"""
    system_prompt = _load_system_prompt()

    # Brave Search で既存なぞなぞを調査
    brave_key = os.environ.get("BRAVE_API_KEY", "")
    evidence = search_riddle_evidence(req.answer, api_key=brave_key)

    # ユーザープロンプト組み立て
    user_parts = [f"問題文: {req.question}", f"答え: {req.answer}"]
    if evidence is None:
        user_parts.append("\n## ウェブ検索結果（検索不可）\n検索APIに接続できませんでした。オリジナリティはLLMの知識のみで判定してください。")
    elif evidence["hit_count"] == 0:
        user_parts.append(f"\n## ウェブ検索結果\n検索クエリ: 「{req.answer} なぞなぞ」\n検索ヒット数: 0\n類似するなぞなぞはウェブ上に見つかりませんでした。")
    else:
        snippet_text = "\n".join(f"- {s}" for s in evidence["snippets"])
        user_parts.append(
            f"\n## ウェブ検索結果\n検索クエリ: 「{req.answer} なぞなぞ」\n検索ヒット数: {evidence['hit_count']}\n\n{snippet_text}"
        )
    user_prompt = "\n".join(user_parts)

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
```

ファイル先頭に `import os` と `from riddle.brave_search import search_riddle_evidence` を追加。

**Step 4: テストが通ることを確認**

Run: `uv run pytest tests/test_scorer_server.py -v`
Expected: 全テスト PASS（既存テストも新テストも）

**Step 5: Commit**

```bash
git add src/riddle/scorer_server.py tests/test_scorer_server.py
git commit -m "feat: integrate Brave Search into scorer for evidence-based originality"
```

---

### Task 4: scorer_prompt.md にウェブ検索エビデンス判定ルールを追加

**Files:**
- Modify: `src/riddle/scorer_prompt.md`

**Step 1: オリジナリティの採点基準を検索エビデンスベースに変更**

`strict_score の採点基準` テーブルのオリジナリティ行と、採点ルールを変更する。

変更前:
```
| オリジナリティ | 2.5 | 既視感のなさ。既存のなぞなぞと構造・答えの両方が異なるか |
```

変更後:
```
| オリジナリティ | 2.5 | **ウェブ検索結果に基づいて判定**。同一/酷似のなぞなぞが見つかったか |
```

採点ルールに追加:
```
- **オリジナリティは検索結果で判定する**（LLMの直感・記憶ではなく事実で判定）:
  - 検索ヒット数が多く、スニペットに同一問題が見つかった → オリジナリティ = 0
  - 検索ヒットはあるが、同じ答えでも問題の構造が異なる → オリジナリティ減点するが0にはしない
  - 検索ヒットがない or 類似なぞなぞが見つからない → オリジナリティ減点しない
  - 検索不可の場合 → LLMの知識で控えめに判定（確信がない限り中間値）
```

**Step 2: 既存テスト通ることを確認**

Run: `uv run pytest tests/ -v`
Expected: 全テスト PASS

**Step 3: Commit**

```bash
git add src/riddle/scorer_prompt.md
git commit -m "feat: scorer judges originality by web search evidence, not LLM intuition"
```

---

### Task 5: .env の BRAVE_API_KEY を scorer_server のプロセスに伝搬確認

**Files:**
- Modify: `src/riddle/scorer_server.py` (main 関数内の .env 読み込みは既にある)
- Check: `src/riddle/service.py` (scorer 子プロセス起動時に env が渡るか)

**Step 1: service.py の scorer 起動を確認**

service.py の scorer 子プロセス起動部分を読み、`os.environ` が子プロセスに継承されることを確認する。
scorer_server.py の `main()` は既に .env を自力で読み込んでいるので、追加変更は不要のはず。

Run: `uv run pytest tests/ -v`
Expected: 全テスト PASS

**Step 2: Commit (変更があれば)**

不要なら skip。

---

### Task 6: E2E テスト

**Step 1: 実際に riddle を実行して検索統合が動作するか確認**

Run:
```bash
cd /root/work/AIRiddleMaker && echo "" | uv run riddle --pattern pun --max-retries 10 --trace 2>&1 | tee /tmp/riddle_e2e_search_test.log
```

**確認ポイント:**
1. scorer が起動してエラーなし
2. 採点ログに「ウェブ検索結果」が含まれている（trace で確認）
3. 検索結果がオリジナリティ判定に反映されている
4. 最終的に合格する問題が生成される

**Step 2: ログを確認**

```bash
grep -i "検索\|search\|brave\|ヒット" /tmp/riddle_e2e_search_test.log
```

**Step 3: 成功したら最終 commit + push**

```bash
git add -A
git commit -m "feat: Brave Search integration for evidence-based originality scoring

scorer_server.py:
- Search '{answer} なぞなぞ' via Brave API before LLM scoring
- Inject hit count + snippets into scorer LLM prompt
- Graceful fallback when search fails

brave_search.py:
- New module wrapping Brave Web Search API
- Returns hit_count + top snippets, None on error

scorer_prompt.md:
- Originality judged by web search evidence, not LLM intuition
- Clear rules for hit/no-hit/search-unavailable cases"

git push origin tune/prompt-v2
```
