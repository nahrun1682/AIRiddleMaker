# Ephemeral CODEX_HOME Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `generate_riddle()` 実行ごとに使い捨てCODEX_HOMEを作り、過去セッション漏洩を構造的に不可能にする

**Architecture:** 現在の `~/.riddle-codex` 固定ディレクトリ＋ `_STALE_ITEMS` クリーンアップ方式を廃止。`generate_riddle()` のたびに `tempfile.mkdtemp()` で一時ディレクトリを作成し、`_SYNC_ITEMS`（AGENTS.md, .codex/, auth.json）のみコピー。Codex 終了後に `shutil.rmtree()` で破棄。`SessionTailer` は一時ディレクトリ内の sessions/ を参照するよう変更。

**Tech Stack:** Python 3.12, tempfile, shutil, pytest

---

### Task 1: `_sync_runtime_home` → `_create_ephemeral_home` リファクタ（テスト）

**Files:**
- Modify: `tests/test_service.py`

**Step 1: Write the failing tests**

既存の `_sync_runtime_home` mock を使うテストは全てスキップせず壊す。新しいテストを追加:

```python
def test_generate_riddle_uses_ephemeral_home(service, tmp_path):
    """Each generate_riddle call creates a fresh temp dir that is removed after."""
    output = {
        "question": "q", "answer": "a", "pattern": "pun",
        "score": {
            "uniqueness": True, "single_paradox": True,
            "observation_based": True, "strict_score": 9.6,
            "passed": True, "reason": "r", "strict_review": "s",
        },
        "attempts": 1,
    }
    output_file = tmp_path / "out.txt"
    output_file.write_text(json.dumps(output))

    codex_home_used = None

    def capture_run(cmd, **kwargs):
        nonlocal codex_home_used
        env = kwargs.get("env", {})
        codex_home_used = env.get("CODEX_HOME")
        return _mock_run(output)

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    with patch("riddle.service.subprocess.run", side_effect=capture_run), \
         patch("riddle.service._OUTPUT_FILE", output_file), \
         patch("riddle.service.subprocess.Popen", return_value=mock_proc), \
         patch("riddle.service.urllib.request.urlopen"):
        service.generate_riddle()

    # Ephemeral dir was used and is now gone
    assert codex_home_used is not None
    assert not Path(codex_home_used).exists(), "Ephemeral dir should be cleaned up"


def test_ephemeral_home_contains_sync_items(service, tmp_path):
    """Ephemeral dir must contain AGENTS.md, .codex/, auth.json from source."""
    # Populate source_home
    source = service._source_home
    source.mkdir(parents=True, exist_ok=True)
    (source / "AGENTS.md").write_text("# test")
    codex_dir = source / ".codex"
    codex_dir.mkdir()
    (codex_dir / "config.toml").write_text("model = 'test'")
    (source / "auth.json").write_text('{"auth_mode": "apikey"}')

    output = {
        "question": "q", "answer": "a", "pattern": "pun",
        "score": {
            "uniqueness": True, "single_paradox": True,
            "observation_based": True, "strict_score": 9.6,
            "passed": True, "reason": "r", "strict_review": "s",
        },
        "attempts": 1,
    }
    output_file = tmp_path / "out.txt"
    output_file.write_text(json.dumps(output))

    contents_snapshot = {}

    def capture_run(cmd, **kwargs):
        env = kwargs.get("env", {})
        home = Path(env["CODEX_HOME"])
        # Snapshot contents while ephemeral dir exists
        contents_snapshot["agents"] = (home / "AGENTS.md").exists()
        contents_snapshot["codex_dir"] = (home / ".codex").is_dir()
        contents_snapshot["auth"] = (home / "auth.json").exists()
        # No stale items should exist
        contents_snapshot["no_sessions"] = not (home / "sessions").exists()
        contents_snapshot["no_tmp"] = not (home / "tmp").exists()
        return _mock_run(output)

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    with patch("riddle.service.subprocess.run", side_effect=capture_run), \
         patch("riddle.service._OUTPUT_FILE", output_file), \
         patch("riddle.service.subprocess.Popen", return_value=mock_proc), \
         patch("riddle.service.urllib.request.urlopen"):
        service.generate_riddle()

    assert contents_snapshot["agents"]
    assert contents_snapshot["codex_dir"]
    assert contents_snapshot["auth"]
    assert contents_snapshot["no_sessions"]
    assert contents_snapshot["no_tmp"]
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_service.py -v --tb=short`
Expected: 2 new tests FAIL

**Step 3: Commit failing tests**

```bash
git add tests/test_service.py
git commit -m "test: add failing tests for ephemeral CODEX_HOME"
```

---

### Task 2: `_create_ephemeral_home` 実装

**Files:**
- Modify: `src/riddle/service.py`

**Step 1: Replace `_sync_runtime_home` + `_STALE_ITEMS` with `_create_ephemeral_home`**

変更点:
1. `_STALE_ITEMS` 定数を削除
2. `_sync_runtime_home()` メソッドを削除
3. `__init__` から `_sync_runtime_home()` 呼び出しを削除。`self.codex_home` もインスタンス化時は設定不要（後方互換のため `self._source_home` のみ保持）
4. 新メソッド `_create_ephemeral_home()` を追加:

```python
import tempfile

def _create_ephemeral_home(self) -> Path:
    """Create a disposable CODEX_HOME with only config files, no history."""
    ephemeral = Path(tempfile.mkdtemp(prefix="riddle-codex-"))
    for item in _SYNC_ITEMS:
        src = self._source_home / item
        dst = ephemeral / item
        if not src.exists():
            continue
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    return ephemeral
```

5. `generate_riddle()` 内で使用:

```python
ephemeral_home = self._create_ephemeral_home()
try:
    env = {
        **os.environ,
        **_load_dotenv(Path(__file__).parent.parent.parent / ".env"),
        "CODEX_HOME": str(ephemeral_home),
    }
    # ... (scorer + codex exec + trace は ephemeral_home を参照)
finally:
    shutil.rmtree(ephemeral_home, ignore_errors=True)
```

6. `SessionTailer` の `codex_home` 引数を `ephemeral_home` に変更

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/test_service.py -v --tb=short`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add src/riddle/service.py
git commit -m "feat: use ephemeral CODEX_HOME per generate_riddle call"
```

---

### Task 3: 既存テスト修正

**Files:**
- Modify: `tests/test_service.py`

**Step 1: Update fixture and existing tests**

`service` fixture を更新:
- `_sync_runtime_home` の mock は不要になる（メソッドが存在しない）
- `service.codex_home` に依存するテストは `service._source_home` 経由に変更

`test_generate_riddle_sets_codex_home` を更新:
- `CODEX_HOME` が一時ディレクトリのパスであること（`.codex-home` 固定文字列でなく `riddle-codex-` prefix を含む）を検証

`test_stale_items_includes_tmp_and_sessions` を削除（`_STALE_ITEMS` 自体が消える）

**Step 2: Run full test suite**

Run: `uv run pytest tests/ -v --tb=short`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add tests/test_service.py
git commit -m "test: update service tests for ephemeral CODEX_HOME"
```

---

### Task 4: `test_subagent_config.py` 更新

**Files:**
- Modify: `tests/test_subagent_config.py`

**Step 1: Check and update**

`_STALE_ITEMS` をインポートしているテストがあれば削除/更新。

**Step 2: Run tests**

Run: `uv run pytest tests/test_subagent_config.py -v --tb=short`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add tests/test_subagent_config.py
git commit -m "test: remove stale items assertion from subagent config tests"
```

---

### Task 5: E2E 動作確認

**Step 1: 実行して過去セッション参照がないことを確認**

```bash
cd /root/work/AIRiddleMaker && echo "動物" | uv run riddle --max-retries 5 --trace 2>&1 | tee /tmp/riddle_ephemeral_test.log
```

確認ポイント:
- `scorer` は定義済みです。過去セッションを手掛かりに` が出ないこと
- `mcp__scorer__score_riddle` が正常に呼び出されること
- `/tmp/riddle-codex-*` ディレクトリが実行後に残っていないこと

```bash
ls /tmp/riddle-codex-* 2>&1  # "No such file or directory" であること
```

**Step 2: Commit all if not already committed**

```bash
git status
```
