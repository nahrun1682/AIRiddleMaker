# Config Model Decoupling Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** riddle.toml の model 値を変更してもテストが壊れない設計にし、scorer 二重定義を修正し、model を gpt-5.4-mini に変更する

**Architecture:** test_main.py の各テストが実プロジェクトの riddle.toml を読んでいるのが根本原因。`monkeypatch.setenv("RIDDLE_CONFIG_FILE", ...)` で存在しないパスを指定し、config.py のデフォルト値（`gpt-5.3-codex`）でアサートする設計に変更。riddle.toml 自体は二重 scorer を修正し model を `gpt-5.4-mini` に。

**Tech Stack:** Python 3.12, pytest, monkeypatch

---

### Task 1: riddle.toml 修正

**Files:**
- Modify: `riddle.toml`

**Step 1: Fix riddle.toml**

重複 `[scorer]` セクションを1つに統合し、top-level model を `gpt-5.4-mini` に変更:

```toml
model = "gpt-5.4-mini"
reasoning_effort = "medium"
max_retries = 10
strict_threshold = 6.0
require_reason_fields = true
trace_default = false

[scorer]
model = "gpt-5.4"
port = 19120
```

**Step 2: Validate TOML parses correctly**

Run: `uv run python -c "import tomllib; d = tomllib.load(open('riddle.toml','rb')); print(d)"`
Expected: dict with single `scorer` key

**Step 3: Commit**

```bash
git add riddle.toml
git commit -m "fix: remove duplicate scorer section, set model to gpt-5.4-mini"
```

---

### Task 2: test_main.py をriddle.tomlから分離（テスト RED）

**Files:**
- Modify: `tests/test_main.py`

**Step 1: 全テストにmonkeypatch追加して期待値を変更**

`test_main_outputs_riddle` と `test_main_theme_shown_in_output` と `test_main_error_exits` は `generate_riddle` の引数をアサートしていないので変更不要。

以下5テストが対象:
- `test_main_pattern_option`
- `test_main_prompts_for_theme_when_not_given`
- `test_main_max_retries_option`
- `test_main_trace_option`
- `test_main_uses_config_values`（既に mock 済み — 影響軽微）

各テストに `monkeypatch` fixture を追加し、先頭で:
```python
monkeypatch.setenv("RIDDLE_CONFIG_FILE", "/tmp/nonexistent-riddle-test.toml")
```

アサーション値を config.py のデフォルト値に合わせる:
- `model="gpt-5.3-codex"` (was `"gpt-5.4"`)
- `scorer_model="gpt-5.4"` (同じ — デフォルトが `"gpt-5.4"`)
- `scorer_port=19120` (同じ)

**Step 2: Run tests to verify they PASS**

Run: `uv run pytest tests/test_main.py -v --tb=short`
Expected: 8 passed

**Step 3: Verify riddle.toml change doesn't break tests**

Run: `uv run pytest tests/ -v --tb=short`
Expected: ALL PASS

**Step 4: Commit**

```bash
git add tests/test_main.py
git commit -m "test: decouple test_main from riddle.toml file contents"
```

---

### Task 3: test_config.py の実ファイル依存テスト更新

**Files:**
- Modify: `tests/test_config.py`

**Step 1: Update `test_riddle_toml_has_scorer_section`**

このテストは実 `riddle.toml` を読んで `[scorer]` セクションの存在を確認する統合テスト。model の値を直接アサートしていないのでそのまま PASS するはず。

確認のみ:

Run: `uv run pytest tests/test_config.py -v --tb=short`
Expected: 6 passed

変更が不要なら commit なし。

---

### Task 4: test_service.py のハードコード確認

**Files:**
- Review: `tests/test_service.py`

**Step 1: 確認**

`test_generate_riddle_sets_codex_home` は `"gpt-5.3-codex"` をアサートしている。これは `service.generate_riddle()` のデフォルト引数値であり、riddle.toml に依存していない。問題なし。

Run: `uv run pytest tests/ -v --tb=short`
Expected: ALL PASS (49 tests)

**Step 2: Commit if any changes were needed**

変更不要なら commit なし。

---

### Task 5: 全テスト最終確認 + E2E

**Step 1: Full test suite**

Run: `uv run pytest tests/ -v --tb=short`
Expected: ALL PASS

**Step 2: E2E — riddle.toml の model が反映されることを確認**

```bash
uv run python -c "
from riddle.config import load_riddle_config
from pathlib import Path
c = load_riddle_config(Path('riddle.toml'))
print(f'codex model: {c.model}')
print(f'scorer model: {c.scorer_model}')
print(f'scorer port: {c.scorer_port}')
"
```

Expected:
```
codex model: gpt-5.4-mini
scorer model: gpt-5.4
scorer port: 19120
```
