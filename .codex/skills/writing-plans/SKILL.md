---
name: writing-plans
description: 仕様や要件があり、複数ステップ作業をコード着手前に計画化するときに使う
---

# 計画を書く

## 概要

実装者がこのコードベースの文脈をまったく知らず、センスもやや怪しい前提で、包括的な実装計画を書く。各タスクでどのファイルを触るか、必要なコード、テスト、確認すべきドキュメント、テスト方法まで、必要情報をすべて記載する。計画全体を小さなタスクに分解する。DRY。YAGNI。TDD。頻繁コミット。

実装者は有能な開発者だが、私たちのツールセットや問題領域はほぼ知らない前提にする。良いテスト設計もあまり得意でない前提にする。

**開始時に宣言:** "I'm using the writing-plans skill to create the implementation plan."

**文脈:** 専用 worktree（brainstorming で作成）で実施。

**保存先:** `docs/plans/YYYY-MM-DD-<feature-name>.md`

## タスク粒度

**1ステップ=1アクション（2〜5分）:**
- "失敗するテストを書く" - 1ステップ
- "実行して失敗を確認する" - 1ステップ
- "テストが通る最小コードを実装する" - 1ステップ
- "テストを実行して成功を確認する" - 1ステップ
- "コミットする" - 1ステップ

## 計画ドキュメントヘッダー

**全計画は次で開始:**

```markdown
# [Feature Name] Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

## タスク構造

```markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/path/test.py::test_name -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
```

## 覚えること
- ファイルパスは常に正確
- 抽象指示でなく具体コードを書く
- コマンドは期待結果つき
- 関連スキルは `@` で参照
- DRY, YAGNI, TDD, 頻繁コミット

## 実行引き渡し

保存後に次を提示:

**"計画が完了し、`docs/plans/<filename>.md` に保存しました。実行方法は2つあります:**

**1. Subagent-Driven（同セッション）** - タスクごとに新規サブエージェントを起動し、タスク間でレビューしながら高速に反復

**2. Parallel Session（別セッション）** - executing-plans で新規セッションを開き、チェックポイント付きでバッチ実行

**どちらで進めますか？"**

**Subagent-Driven 選択時:**
- **REQUIRED SUB-SKILL:** superpowers:subagent-driven-development を使用
- このセッション内で進行
- タスクごとに新規サブエージェント + コードレビュー

**Parallel Session 選択時:**
- worktree 上で新規セッションを開くよう案内
- **REQUIRED SUB-SKILL:** 新セッションで superpowers:executing-plans を使用
