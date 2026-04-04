---
name: using-git-worktrees
description: 現在ワークスペースから分離して機能開発を始めるとき、または実装計画実行前に使う。適切なディレクトリ選択と安全確認を行い、隔離 git worktree を作成する。
---

# Git Worktree の使い方

## 概要

Git worktree は同一リポジトリを共有しつつ、切り替えなしで複数ブランチを同時に作業できる隔離ワークスペースを作る。

**コア原則:** 体系的なディレクトリ選択 + 安全確認 = 信頼できる隔離。

**開始時に宣言:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## ディレクトリ選択手順

次の優先順で判断する:

### 1. 既存ディレクトリを確認

```bash
# 優先順で確認
ls -d .worktrees 2>/dev/null     # 優先（hidden）
ls -d worktrees 2>/dev/null      # 代替
```

**見つかった場合:** そのディレクトリを使う。両方ある場合は `.worktrees` を優先。

### 2. CLAUDE.md を確認

```bash
grep -i "worktree.*director" CLAUDE.md 2>/dev/null
```

**指定がある場合:** 質問せず、その指定を使う。

### 3. ユーザーに確認

ディレクトリが存在せず、CLAUDE.md 指定もない場合:

```
No worktree directory found. Where should I create worktrees?

1. .worktrees/ (project-local, hidden)
2. ~/.config/superpowers/worktrees/<project-name>/ (global location)

Which would you prefer?
```

## 安全確認

### プロジェクトローカル（.worktrees / worktrees）の場合

**作成前に、必ず ignore 済みか検証する:**

```bash
# ignore 判定（local/global/system の gitignore を反映）
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```

**ignore されていない場合:**

Jesse のルール "Fix broken things immediately" に従う:
1. `.gitignore` に適切な行を追加
2. その変更をコミット
3. その後 worktree 作成を続行

**重要理由:** worktree 内容の誤コミットを防ぐため。

### グローバルディレクトリ（~/.config/superpowers/worktrees）の場合

プロジェクト外なので `.gitignore` 確認は不要。

## 作成手順

### 1. プロジェクト名を検出

```bash
project=$(basename "$(git rev-parse --show-toplevel)")
```

### 2. Worktree 作成

```bash
# フルパス決定
case $LOCATION in
  .worktrees|worktrees)
    path="$LOCATION/$BRANCH_NAME"
    ;;
  ~/.config/superpowers/worktrees/*)
    path="~/.config/superpowers/worktrees/$project/$BRANCH_NAME"
    ;;
esac

# 新規ブランチで worktree 作成
git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

### 3. プロジェクトセットアップ実行

自動判定して適切なセットアップを実行:

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Rust
if [ -f Cargo.toml ]; then cargo build; fi

# Python
if [ -f pyproject.toml ]; then uv sync; fi

# Go
if [ -f go.mod ]; then go mod download; fi
```

### 4. クリーンな初期状態を検証

worktree がクリーンに始まるかテスト実行:

```bash
# 例: プロジェクトに合わせたコマンドを使う
npm test
cargo test
uv run pytest
go test ./...
```

**テスト失敗時:** 失敗内容を報告し、続行するか調査するか確認。

**テスト成功時:** 準備完了を報告。

### 5. 場所を報告

```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## クイックリファレンス

| Situation | Action |
|-----------|--------|
| `.worktrees/` が存在 | それを使う（ignore確認） |
| `worktrees/` が存在 | それを使う（ignore確認） |
| 両方存在 | `.worktrees/` を使う |
| どちらもない | CLAUDE.md 確認 → ユーザー確認 |
| ignore されていない | `.gitignore` 追加 + コミット |
| 初期テストで失敗 | 失敗報告 + 方針確認 |
| package.json/Cargo.toml なし | 依存導入をスキップ |

## よくあるミス

### ignore 確認を飛ばす

- **問題:** worktree 内容が追跡され、git status が汚染
- **対処:** プロジェクトローカル作成前に必ず `git check-ignore`

### ディレクトリ位置を決め打ち

- **問題:** 一貫性を崩し、プロジェクト規約違反
- **対処:** 優先順を守る: existing > CLAUDE.md > ask

### テスト失敗のまま進む

- **問題:** 新規不具合と既存不具合の区別がつかない
- **対処:** 失敗報告し、明示許可を得てから進む

### セットアップコマンドをハードコード

- **問題:** 異なるツールチェーンのプロジェクトで壊れる
- **対処:** プロジェクトファイルから自動判定（package.json など）

## 実行例

```
You: I'm using the using-git-worktrees skill to set up an isolated workspace.

[Check .worktrees/ - exists]
[Verify ignored - git check-ignore confirms .worktrees/ is ignored]
[Create worktree: git worktree add .worktrees/auth -b feature/auth]
[Run npm install]
[Run npm test - 47 passing]

Worktree ready at /Users/jesse/myproject/.worktrees/auth
Tests passing (47 tests, 0 failures)
Ready to implement auth feature
```

## レッドフラグ

**Never:**
- ignore 確認なしで worktree 作成（project-local）
- 初期テスト確認を省略
- テスト失敗のまま無確認で進行
- 曖昧なときに保存先を決め打ち
- CLAUDE.md 確認を省略

**Always:**
- 優先順を守る: existing > CLAUDE.md > ask
- project-local では ignore 状態を確認
- 自動判定でセットアップ実行
- クリーンなテスト初期状態を確認

## 連携

**呼び出し元:**
- **brainstorming**（Phase 4）- 設計承認後に実装へ進む場合は REQUIRED
- **subagent-driven-development** - タスク実行前に REQUIRED
- **executing-plans** - タスク実行前に REQUIRED
- そのほか隔離ワークスペースが必要なスキル

**併用先:**
- **finishing-a-development-branch** - 作業完了後の cleanup で REQUIRED
