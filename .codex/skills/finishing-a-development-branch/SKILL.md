---
name: finishing-a-development-branch
description: 実装完了・全テスト成功後に、作業の統合方法（マージ/PR/保持/破棄）を選び、完了まで進めるときに使う
---

# 開発ブランチを完了させる

## 概要

明確な選択肢を提示し、選ばれたワークフローを実行して開発作業を完了させる。

**コア原則:** テスト検証 → 選択肢提示 → 選択実行 → 後片付け。

**開始時に宣言:** "I'm using the finishing-a-development-branch skill to complete this work."

## プロセス

### Step 1: テストを検証する

**選択肢を提示する前に、テスト成功を確認する:**

```bash
# プロジェクトのテストスイートを実行
npm test / cargo test / uv run pytest / go test ./...
```

**テスト失敗時:**
```
Tests failing (<N> failures). Must fix before completing:

[Show failures]

Cannot proceed with merge/PR until tests pass.
```

ここで停止。Step 2 へ進まない。

**テスト成功時:** Step 2 へ進む。

### Step 2: ベースブランチを特定する

```bash
# よくあるベースブランチを試す
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

または確認する: "This branch split from main - is that correct?"

### Step 3: 選択肢を提示する

次の 4 つを正確に提示する:

```
Implementation complete. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)
4. Discard this work

Which option?
```

**説明を追加しない** - 簡潔に提示する。

### Step 4: 選択を実行する

#### Option 1: ローカルでマージ

```bash
# ベースブランチへ切り替え
git checkout <base-branch>

# 最新を取得
git pull

# フィーチャーブランチをマージ
git merge <feature-branch>

# マージ結果でテスト検証
<test command>

# テスト成功なら
git branch -d <feature-branch>
```

その後: worktree をクリーンアップ（Step 5）

#### Option 2: Push して PR 作成

```bash
# ブランチを push
git push -u origin <feature-branch>

# PR を作成
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<2-3 bullets of what changed>

## Test Plan
- [ ] <verification steps>
EOF
)"
```

その後: worktree をクリーンアップ（Step 5）

#### Option 3: 現状維持

報告: "Keeping branch <name>. Worktree preserved at <path>."

**worktree はクリーンアップしない。**

#### Option 4: 破棄

**必ず先に確認:**
```
This will permanently delete:
- Branch <name>
- All commits: <commit-list>
- Worktree at <path>

Type 'discard' to confirm.
```

厳密一致の確認入力を待つ。

確認後:
```bash
git checkout <base-branch>
git branch -D <feature-branch>
```

その後: worktree をクリーンアップ（Step 5）

### Step 5: worktree をクリーンアップ

**Option 1, 2, 4 の場合:**

worktree か確認:
```bash
git worktree list | grep $(git branch --show-current)
```

該当するなら:
```bash
git worktree remove <worktree-path>
```

**Option 3:** worktree を保持。

## クイックリファレンス

| Option | Merge | Push | Keep Worktree | Cleanup Branch |
|--------|-------|------|---------------|----------------|
| 1. Merge locally | ✓ | - | - | ✓ |
| 2. Create PR | - | ✓ | ✓ | - |
| 3. Keep as-is | - | - | ✓ | - |
| 4. Discard | - | - | - | ✓ (force) |

## よくあるミス

**テスト検証を飛ばす**
- **問題:** 壊れたコードをマージ/失敗する PR を作る
- **対処:** 選択肢提示前に必ずテストを検証

**自由記述の質問**
- **問題:** "What should I do next?" は曖昧
- **対処:** 構造化された 4 選択肢を正確に提示

**自動で worktree を消す**
- **問題:** 後で必要な worktree を消す（Option 2, 3）
- **対処:** クリーンアップは Option 1 と 4 のみ

**破棄の確認なし**
- **問題:** 誤って作業を削除
- **対処:** 必ず "discard" の入力確認を要求

## レッドフラグ

**絶対にしない:**
- テスト失敗のまま進める
- マージ結果のテスト検証なしにマージ
- 確認なしで作業削除
- 明示依頼なしの force-push

**必ず行う:**
- 選択肢提示前のテスト検証
- 正確に 4 つの選択肢提示
- Option 4 の typed confirmation
- Option 1 と 4 のみ worktree クリーンアップ

## 連携

**呼び出し元:**
- **subagent-driven-development**（Step 7）- 全タスク完了後
- **executing-plans**（Step 5）- 全バッチ完了後

**併用先:**
- **using-git-worktrees** - そのスキルで作成した worktree を片付ける
