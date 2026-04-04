---
name: executing-plans
description: レビュー用チェックポイントを挟みつつ、別セッションで実行する実装計画があるときに使う
---

# 計画の実行

## 概要

計画を読み込み、批判的にレビューし、タスクをバッチ単位で実行し、バッチ間でレビュー報告する。

**中核原則:** アーキテクトレビュー用チェックポイント付きのバッチ実行。

**開始時に宣言:** "I'm using the executing-plans skill to implement this plan."

## プロセス

### Step 1: 計画の読み込みとレビュー
1. 計画ファイルを読む
2. 批判的にレビューし、疑問点や懸念点を洗い出す
3. 懸念がある場合: 開始前に人間パートナーへ共有
4. 懸念がない場合: TodoWrite を作成して進行

### Step 2: バッチ実行
**デフォルト: 最初の3タスク**

各タスクについて:
1. `in_progress` にする
2. 計画の手順を正確に実行する
3. 指定された検証を行う
4. `completed` にする

### Step 3: 報告
バッチ完了時:
- 実装内容を示す
- 検証出力を示す
- "Ready for feedback." と伝える

### Step 4: 継続
フィードバックに応じて:
- 必要なら修正を反映
- 次バッチを実行
- 完了まで繰り返す

### Step 5: 開発完了処理
全タスク完了・検証後:
- "I'm using the finishing-a-development-branch skill to complete this work." と宣言
- **REQUIRED SUB-SKILL:** superpowers:finishing-a-development-branch
- その指示に従ってテスト検証、選択肢提示、実行

## 停止して確認すべき条件

**以下では即停止:**
- バッチ途中でブロッカー発生（依存不足、テスト失敗、指示不明）
- 計画に重大欠落があり開始不能
- 指示理解不能
- 検証が繰り返し失敗

**推測で進めず、明確化を依頼する。**

## 前段へ戻る条件

**Step 1 へ戻る:**
- パートナーが計画を更新した
- 根本アプローチの再検討が必要

**ブロッカーを強行突破しない。**

## 覚えること
- 先に批判的レビュー
- 手順厳守
- 検証省略禁止
- 計画指定のスキル参照
- バッチ間は報告して待機
- 詰まったら停止して確認
- 明示同意なしで main/master で実装開始しない

## 連携

**必須ワークフロースキル:**
- **superpowers:using-git-worktrees** - 開始前に分離ワークスペース作成
- **superpowers:writing-plans** - 本スキルが実行する計画を作成
- **superpowers:finishing-a-development-branch** - 全タスク完了後の終了処理
