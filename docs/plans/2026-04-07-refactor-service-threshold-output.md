# Service Refactor A Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `RiddleService` の責務集中を解消し、`strict_threshold` 判定を一元化し、Codex出力を固定パスではなく実行ごとの一時ファイルに切り替える。

**Architecture:** `src/riddle/service.py` から「CODEX_HOME準備」「scorerプロセス管理」「codex実行」「出力JSON検証」を分離し、サービス本体はオーケストレーションだけを担当する。`ScoreDetail` の固定閾値バリデーションを削除し、合否判定は `RiddleService` 側の単一ロジックで行う。`-o` 出力先は `tempfile` で毎回ユニークなファイルを割り当て、実行後に必ず削除する。

**Tech Stack:** Python 3.12, pytest, pydantic v2, subprocess, tempfile, pathlib

---

### Task 1: service分割のための失敗テストを追加

**Files:**
- Modify: `tests/test_service.py`

**Step 1: 一時出力ファイル利用を検証する失敗テストを追加**

```python
def test_generate_riddle_uses_unique_temp_output_file(service):
    ...
    # subprocess.run の引数から -o の値を抜き出して記録
    # 実行ごとに異なるパスで、/tmp 配下の riddle-output- プレフィックスを期待
```

**Step 2: 出力ファイルがクリーンアップされる失敗テストを追加**

```python
def test_generate_riddle_removes_temp_output_file_after_parse(service):
    ...
    # side_effect で出力ファイルを作成
    # generate_riddle() 後に Path(output_path).exists() is False を期待
```

**Step 3: 既存の `_OUTPUT_FILE` パッチ依存テストを新方式に置換（この時点でREDにする）**

- `patch("riddle.service._OUTPUT_FILE", output_file)` を使っているテストを修正。
- `subprocess.run` モックの side_effect で `-o` 先へ JSON を書き込むヘルパーに置換。

**Step 4: 失敗確認**

Run: `uv run pytest tests/test_service.py -v --tb=short`
Expected: FAIL（固定 `_OUTPUT_FILE` 前提が崩れたテスト、または temp output 未実装）

**Step 5: Commit（テストのみ）**

```bash
git add tests/test_service.py
git commit -m "test: add red tests for temp output file behavior"
```

---

### Task 2: service.py を責務分割して最小実装でテストを通す

**Files:**
- Modify: `src/riddle/service.py`
- Test: `tests/test_service.py`

**Step 1: CODEX_HOME管理クラスを追加**

```python
class CodexHomeManager:
    def __init__(self, source_home: Path, sync_items: list[str]): ...
    def create(self) -> Path: ...
    def cleanup(self, path: Path) -> None: ...
```

- 既存 `_create_ephemeral_home()` のロジックを移管。

**Step 2: scorerサーバー管理クラスを追加**

```python
class ScorerProcessManager:
    def start(self, port: int, model: str, env: dict[str, str]) -> subprocess.Popen: ...
    def stop(self, proc: subprocess.Popen) -> None: ...
```

- 既存 `_start_scorer_server()` と終了処理を移管。

**Step 3: codex実行クラスを追加**

```python
class CodexExecRunner:
    def run(..., output_path: Path, ... ) -> subprocess.CompletedProcess[str]: ...
```

- `codex exec ... -o <path>` 組み立てを移管。

**Step 4: 出力パーサクラスを追加**

```python
class RiddleOutputParser:
    def parse(self, output_path: Path) -> RiddleResult: ...
```

- JSONロードと `RiddleResult.model_validate()` をここへ移す。

**Step 5: `RiddleService.generate_riddle()` をオーケストレーション化**

- `tempfile.NamedTemporaryFile(prefix="riddle-output-", suffix=".json", delete=False)` で出力先作成。
- manager群を呼び出し。
- finallyで `ephemeral_home` と `output_path` を確実に削除。

**Step 6: テスト実行**

Run: `uv run pytest tests/test_service.py -v --tb=short`
Expected: PASS

**Step 7: Commit**

```bash
git add src/riddle/service.py tests/test_service.py
git commit -m "refactor: split service responsibilities and use temp codex output"
```

---

### Task 3: strict_threshold 判定を一元化（models固定閾値を除去）

**Files:**
- Modify: `src/riddle/models.py`
- Modify: `src/riddle/service.py`
- Modify: `tests/test_models.py`
- Modify: `tests/test_service.py`

**Step 1: `ScoreDetail` の固定6.0バリデータを削除してヘルパーメソッド追加**

```python
class ScoreDetail(BaseModel):
    ...
    def expected_pass(self, strict_threshold: float) -> bool:
        return self.structural_soundness and self.concrete_grounding and self.strict_score >= strict_threshold
```

**Step 2: `RiddleService` で `expected_pass(strict_threshold)` を使って合否検証**

- 既存の `expected_pass = (...)` ローカルロジックを削除。
- 一箇所に統一。

**Step 3: modelsテストを更新（RED→GREEN）**

- `test_score_detail_rejects_inconsistent_passed` は削除または仕様変更。
- 新規テスト:

```python
def test_score_detail_expected_pass_uses_given_threshold():
    score = ScoreDetail(... strict_score=7.0, passed=False)
    assert score.expected_pass(6.0) is True
    assert score.expected_pass(8.0) is False
```

**Step 4: serviceテストでstrict_threshold検証を維持**

- `test_generate_riddle_validates_strict_threshold` が継続して通ることを確認。

**Step 5: テスト実行**

Run: `uv run pytest tests/test_models.py tests/test_service.py -v --tb=short`
Expected: PASS

**Step 6: Commit**

```bash
git add src/riddle/models.py src/riddle/service.py tests/test_models.py tests/test_service.py
git commit -m "refactor: centralize strict threshold validation in service flow"
```

---

### Task 4: 回帰確認と最終チェック

**Files:**
- Modify: なし（必要ならテスト修正のみ）

**Step 1: 全体テスト実行**

Run: `uv run pytest -v --tb=short`
Expected: ALL PASS

**Step 2: 主要CLI回帰スモーク**

Run: `uv run pytest tests/test_main.py -v --tb=short`
Expected: PASS

**Step 3: 変更範囲の最終確認**

Run: `git status --short`
Expected: 意図したファイルのみ変更

**Step 4: Commit（最終調整がある場合のみ）**

```bash
git add <adjusted-files>
git commit -m "test: finalize regression fixes for service refactor"
```
