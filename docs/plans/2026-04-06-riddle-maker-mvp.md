# AIRiddleMaker MVP 実装プラン

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Codex CLIをオーケストレーターとして、日本語なぞなぞを生成・検証・採点するCLIツールを構築する

**Architecture:** PythonサービスがCODEX_HOME=.codex-homeでCodex CLIをサブプロセス起動。Codexがなぞなぞ生成→ウェブ検索フィルタ→採点サブエージェントのループを制御し、結果をJSONで返す。PythonはそのJSONをパースしてCLIに表示する。

**Tech Stack:** Python 3.13+, uv, pydantic, pytest, Codex CLI（CODEX_HOME経由）

---

## Task 1: Pythonプロジェクトのセットアップ

**Files:**
- Create: `pyproject.toml`
- Create: `src/riddle/__init__.py`
- Create: `tests/__init__.py`

**Step 1: pyproject.tomlを作成**

```toml
[project]
name = "ai-riddle-maker"
version = "0.1.0"
description = "日本語特化なぞなぞ生成システム"
requires-python = ">=3.13"
dependencies = [
    "pydantic>=2.0",
]

[project.scripts]
riddle = "riddle.main:main"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "black>=24.0",
    "isort>=5.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src --cov-report=term-missing"

[tool.black]
line-length = 88

[tool.isort]
profile = "black"
```

**Step 2: ディレクトリ構造を作成**

```bash
mkdir -p src/riddle tests
touch src/riddle/__init__.py tests/__init__.py
```

**Step 3: 依存関係をインストール**

```bash
uv venv
uv sync --extra dev
```

期待: `.venv/` が作成され、依存パッケージがインストールされる

**Step 4: コミット**

```bash
git add pyproject.toml src/ tests/
git commit -m "feat: initialize Python project with uv"
```

---

## Task 2: Pydanticモデルの作成

**Files:**
- Create: `src/riddle/models.py`
- Create: `tests/test_models.py`

**Step 1: 失敗するテストを書く**

```python
# tests/test_models.py
import pytest
from pydantic import ValidationError
from riddle.models import RiddleResult, ScoreDetail


def test_riddle_result_valid():
    result = RiddleResult(
        question="食べるほど減るのに、食べないと増えるものは？",
        answer="食欲",
        pattern="paradox",
        score=ScoreDetail(uniqueness=True, single_paradox=True, observation_based=True),
        attempts=2,
    )
    assert result.question == "食べるほど減るのに、食べないと増えるものは？"
    assert result.attempts == 2
    assert result.score.uniqueness is True


def test_riddle_result_from_json():
    json_str = """{
        "question": "テスト問題",
        "answer": "テスト答え",
        "pattern": "pun",
        "score": {"uniqueness": true, "single_paradox": false, "observation_based": true},
        "attempts": 1
    }"""
    result = RiddleResult.model_validate_json(json_str)
    assert result.pattern == "pun"


def test_riddle_result_invalid_attempts():
    with pytest.raises(ValidationError):
        RiddleResult(
            question="q", answer="a", pattern="pun",
            score=ScoreDetail(uniqueness=True, single_paradox=True, observation_based=True),
            attempts=0,  # 1以上であるべき
        )
```

**Step 2: テストが失敗することを確認**

```bash
uv run pytest tests/test_models.py -v
```

期待: `ModuleNotFoundError: No module named 'riddle.models'`

**Step 3: モデルを実装**

```python
# src/riddle/models.py
from pydantic import BaseModel, Field


class ScoreDetail(BaseModel):
    uniqueness: bool        # 答えが一意か
    single_paradox: bool   # 一現象一逆説か
    observation_based: bool # 観察ベースか

    @property
    def passed(self) -> bool:
        return self.uniqueness and self.single_paradox and self.observation_based


class RiddleResult(BaseModel):
    question: str
    answer: str
    pattern: str  # paradox / pun / char_extract / reverse_read / char_add_remove / kanji_structure / nazokake
    score: ScoreDetail
    attempts: int = Field(ge=1)
```

**Step 4: テストが通ることを確認**

```bash
uv run pytest tests/test_models.py -v
```

期待: 3件 PASS

**Step 5: コミット**

```bash
git add src/riddle/models.py tests/test_models.py
git commit -m "feat: add RiddleResult and ScoreDetail Pydantic models"
```

---

## Task 3: `.codex-home/` Codex設定の構築

**Files:**
- Create: `.codex-home/config.toml`
- Create: `.codex-home/AGENTS.md`
- Create: `.codex-home/skills/generate.md`
- Create: `.codex-home/agents/scorer.md`

**注意:** このTaskはテスト不要（Codex設定ファイルはプロンプト文書）

**Step 1: config.tomlを作成**

```toml
# .codex-home/config.toml
model = "o4-mini"
model_reasoning_effort = "medium"
web_search = "live"

[features]
multi_agent = true
```

**Step 2: AGENTS.md（リーダー指示）を作成**

```markdown
# AIRiddleMaker リーダーエージェント

あなたは日本語なぞなぞ生成システムのオーケストレーターです。

## タスク

以下のループを最大5回繰り返し、条件を満たすなぞなぞを1問生成してください。

### ループ手順

1. `skills/generate.md` の制約に従い、なぞなぞを1問生成する
2. 生成したなぞなぞ（問題文のみ）をウェブ検索する
   - 検索結果に同一または酷似したなぞなぞが見つかった → ボツ。ループ先頭へ戻る
   - 見つからなかった → 次へ進む
3. 採点サブエージェント（agents/scorer.md）を呼び出し、品質を判定する
   - 判定: NG → ボツ。ループ先頭へ戻る
   - 判定: OK → 出力へ進む

### 出力フォーマット

5回以内に採択できた場合、**必ず以下のJSONのみを出力**してください。他のテキストは一切含めないこと。

```json
{
  "question": "なぞなぞ問題文",
  "answer": "答え",
  "pattern": "paradox",
  "score": {
    "uniqueness": true,
    "single_paradox": true,
    "observation_based": true
  },
  "attempts": 2
}
```

5回試してすべてボツになった場合:

```json
{
  "error": "max_retries_exceeded",
  "attempts": 5
}
```

## パターン一覧

- `paradox`: 逆説・現象系
- `pun`: 同音異義・ダジャレ系
- `char_extract`: 文字分解系
- `reverse_read`: 逆読み・回文系
- `char_add_remove`: 文字足し引き系
- `kanji_structure`: 漢字構造系
- `nazokake`: なぞかけ三段謎
```

**Step 3: skills/generate.md（生成スキル）を作成**

```markdown
# なぞなぞ生成スキル

## 制約

以下の制約に従ってなぞなぞを1問生成してください。

### 禁止事項
- よくある答え（影・時間・風・沈黙・炎・夢）は使わない
- 英語から翻訳したものは使わない
- 定番フォームの連続使用は避ける

### 必須条件
- 答えが一つに定まること（一意性）
- 一つの現象から一つの逆説が成立すること（一現象一逆説）
- 概念遊びより物理現象・日常の観察から生まれていること
- 答えを聞いた瞬間に「なるほど！」の納得感があること

### 日本語固有の活用
以下のいずれかのパターンを使うこと:
- **paradox**: 逆説・現象系（例: 「乾けば乾くほど濡れるものは → タオル」）
- **pun**: 同音異義・ダジャレ系（例: 「食べられないパン → フライパン」）
- **char_extract**: 文字分解系（例: 「機械の真ん中 → 蚊（き**か**い）」）
- **reverse_read**: 逆読み系
- **char_add_remove**: 文字足し引き系（例: 「おしりに『う』をつけると少なくなる野菜 → なす」）
- **kanji_structure**: 漢字構造系
- **nazokake**: なぞかけ三段謎

## 出力フォーマット

以下のJSON形式で出力してください:

```json
{"question": "問題文", "answer": "答え", "pattern": "パターン名"}
```
```

**Step 4: agents/scorer.md（採点エージェント）を作成**

```markdown
# 採点エージェント

あなたはなぞなぞの品質審査員です。以下の3基準で判定してください。

## 判定基準

### ① 一意性（uniqueness）
答えが一つに定まるか。
- OK: 問題文から論理的に答えが一つに絞れる
- NG: 複数の答えが成立する（例: 「屋根にはいるのに家にいないもの」→「ね」も「や」も成立）

### ② 一現象一逆説（single_paradox）
一つの現象から一つの逆説が成立しているか。
- OK: 「乾けば乾くほど濡れる → タオル」（一ステップ）
- NG: 「濡れるほど軽くなる → 雑巾」（濡れる＋絞るの2ステップ）

### ③ 観察ベース（observation_based）
概念ではなく物理現象・日常の事実から生まれているか。
- OK: タオル、卵、つらら などの具体物
- NG: 平和、希望、愛 などの抽象概念

## 入力

判定対象のなぞなぞ:
- 問題: {{question}}
- 答え: {{answer}}

## 出力フォーマット

```json
{
  "uniqueness": true,
  "single_paradox": false,
  "observation_based": true,
  "passed": false,
  "reason": "一現象一逆説の基準を満たしていない。理由: ..."
}
```

`passed` は3つすべてがtrueの場合のみtrue。
```

**Step 5: コミット**

```bash
git add .codex-home/
git commit -m "feat: add .codex-home Codex configuration for riddle generation"
```

---

## Task 4: RiddleServiceの実装

**Files:**
- Create: `src/riddle/service.py`
- Create: `tests/test_service.py`

**Step 1: 失敗するテストを書く**

```python
# tests/test_service.py
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from riddle.models import RiddleResult
from riddle.service import RiddleService


@pytest.fixture
def service():
    return RiddleService()


def test_generate_riddle_success(service):
    mock_output = json.dumps({
        "question": "食べるほど減るのに、食べないと増えるものは？",
        "answer": "食欲",
        "pattern": "paradox",
        "score": {"uniqueness": True, "single_paradox": True, "observation_based": True},
        "attempts": 2,
    })

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = mock_output

    with patch("riddle.service.subprocess.run", return_value=mock_result):
        result = service.generate_riddle()

    assert isinstance(result, RiddleResult)
    assert result.answer == "食欲"
    assert result.attempts == 2


def test_generate_riddle_sets_codex_home(service):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({
        "question": "q", "answer": "a", "pattern": "pun",
        "score": {"uniqueness": True, "single_paradox": True, "observation_based": True},
        "attempts": 1,
    })

    with patch("riddle.service.subprocess.run", return_value=mock_result) as mock_run:
        service.generate_riddle()

    call_kwargs = mock_run.call_args
    env = call_kwargs.kwargs.get("env") or call_kwargs[1].get("env", {})
    assert "CODEX_HOME" in env
    assert ".codex-home" in env["CODEX_HOME"]


def test_generate_riddle_max_retries(service):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"error": "max_retries_exceeded", "attempts": 5})

    with patch("riddle.service.subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="max_retries_exceeded"):
            service.generate_riddle()
```

**Step 2: テストが失敗することを確認**

```bash
uv run pytest tests/test_service.py -v
```

期待: `ModuleNotFoundError: No module named 'riddle.service'`

**Step 3: サービスを実装**

```python
# src/riddle/service.py
import json
import os
import subprocess
from pathlib import Path

from riddle.models import RiddleResult


class RiddleService:
    def __init__(self, codex_home: Path | None = None):
        self.codex_home = codex_home or Path(__file__).parent.parent.parent / ".codex-home"

    def generate_riddle(self, pattern: str | None = None) -> RiddleResult:
        prompt = "なぞなぞを1問生成してください。"
        if pattern:
            prompt += f"パターン: {pattern}"

        output_file = Path("/tmp/riddle_output.txt")
        env = {**os.environ, "CODEX_HOME": str(self.codex_home)}

        result = subprocess.run(
            [
                "codex", "exec",
                "--dangerously-bypass-approvals-and-sandbox",
                "-o", str(output_file),
                prompt,
            ],
            env=env,
            capture_output=True,
            text=True,
        )

        raw = output_file.read_text() if output_file.exists() else result.stdout
        data = json.loads(raw)

        if "error" in data:
            raise RuntimeError(data["error"])

        return RiddleResult.model_validate(data)
```

**Step 4: テストが通ることを確認**

```bash
uv run pytest tests/test_service.py -v
```

期待: 3件 PASS

**Step 5: コミット**

```bash
git add src/riddle/service.py tests/test_service.py
git commit -m "feat: add RiddleService with Codex CLI subprocess invocation"
```

---

## Task 5: CLIエントリポイントの実装

**Files:**
- Create: `src/riddle/main.py`
- Create: `tests/test_main.py`

**Step 1: 失敗するテストを書く**

```python
# tests/test_main.py
from unittest.mock import MagicMock, patch

from riddle.main import main
from riddle.models import RiddleResult, ScoreDetail


def _make_result(**kwargs) -> RiddleResult:
    defaults = dict(
        question="テスト問題", answer="テスト答え", pattern="pun",
        score=ScoreDetail(uniqueness=True, single_paradox=True, observation_based=True),
        attempts=1,
    )
    return RiddleResult(**(defaults | kwargs))


def test_main_outputs_riddle(capsys):
    with patch("riddle.main.RiddleService") as MockService:
        MockService.return_value.generate_riddle.return_value = _make_result()
        main([])

    captured = capsys.readouterr()
    assert "テスト問題" in captured.out
    assert "テスト答え" in captured.out


def test_main_pattern_option(capsys):
    with patch("riddle.main.RiddleService") as MockService:
        MockService.return_value.generate_riddle.return_value = _make_result(pattern="paradox")
        main(["--pattern", "paradox"])

    MockService.return_value.generate_riddle.assert_called_once_with(pattern="paradox")
```

**Step 2: テストが失敗することを確認**

```bash
uv run pytest tests/test_main.py -v
```

**Step 3: CLIを実装**

```python
# src/riddle/main.py
import argparse
import sys

from riddle.service import RiddleService


def main(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="日本語なぞなぞ生成システム")
    parser.add_argument("--pattern", help="生成パターン (paradox/pun/char_extract 等)")
    parsed = parser.parse_args(args)

    service = RiddleService()
    try:
        result = service.generate_riddle(pattern=parsed.pattern)
    except RuntimeError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"問題: {result.question}")
    print(f"答え: {result.answer}")
    print(f"パターン: {result.pattern}")
    print(f"試行回数: {result.attempts}回")
    print(f"採点: 一意性={result.score.uniqueness} / 一現象一逆説={result.score.single_paradox} / 観察ベース={result.score.observation_based}")


if __name__ == "__main__":
    main()
```

**Step 4: テストが通ることを確認**

```bash
uv run pytest tests/test_main.py -v
```

期待: 2件 PASS

**Step 5: 全テスト実行**

```bash
uv run pytest -v
```

期待: 全件 PASS

**Step 6: コミット**

```bash
git add src/riddle/main.py tests/test_main.py
git commit -m "feat: add CLI entry point with --pattern option"
```

---

## Task 6: 動作確認

**Step 1: インストール確認**

```bash
uv run python -m riddle.main --help
```

期待: `usage: main.py [-h] [--pattern PATTERN]` が表示される

**Step 2: 実際に動かしてみる**

```bash
uv run python -m riddle.main
```

Codex CLIが起動し、なぞなぞが生成・検索・採点されて出力されることを確認する。

**Step 3: カバレッジ確認**

```bash
uv run pytest --cov-report=term-missing
```

期待: `src/riddle/` の主要ファイルが80%以上カバー

**Step 4: 最終コミット**

```bash
git add -A
git commit -m "feat: AIRiddleMaker MVP complete"
```

---

## 補足: トラブルシューティング

**Codex CLIが認証エラーを出す場合:**
```bash
codex login
```

**CODEX_HOME配下のスキルが読み込まれない場合:**
- `.codex-home/config.toml` の `[features] multi_agent = true` を確認
- `CODEX_HOME` のパスが絶対パスになっているか確認

**Codex出力がJSONでない場合:**
- `AGENTS.md` の「他のテキストは一切含めないこと」の指示を強化する
- `--output-last-message` オプションで最終メッセージのみ取得する設計になっているので、前置きテキストは除外される
