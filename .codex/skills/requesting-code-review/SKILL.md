---
name: requesting-code-review
description: タスク完了時・主要機能実装時・マージ前に、成果物が要件を満たすか検証するために使う
---

# コードレビュー依頼

問題が連鎖する前に見つけるため、superpowers:code-reviewer サブエージェントを起動する。

**中核原則:** 早くレビューし、頻繁にレビューする。

## レビュー依頼のタイミング

**必須:**
- subagent-driven development の各タスク完了後
- 主要機能の実装完了後
- main へマージする前

**任意だが有効:**
- 行き詰まったとき
- リファクタ前
- 複雑なバグ修正後

## 依頼方法

**1. git SHA を取得**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. code-reviewer サブエージェント起動**

Task ツールで superpowers:code-reviewer を使い、`code-reviewer.md` テンプレートを埋める。

**プレースホルダー:**
- `{WHAT_WAS_IMPLEMENTED}` - 実装内容
- `{PLAN_OR_REQUIREMENTS}` - 満たすべき要件
- `{BASE_SHA}` - 開始コミット
- `{HEAD_SHA}` - 終了コミット
- `{DESCRIPTION}` - 簡易要約

**3. フィードバックに対応**
- Critical は即修正
- Important は先へ進む前に修正
- Minor は後で対応
- 誤指摘は根拠付きで反論

## 例

```
[Task 2: 検証関数追加を完了]

You: 先に進む前にレビュー依頼する。

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[superpowers:code-reviewer 起動]
  WHAT_WAS_IMPLEMENTED: 会話インデックスの検証・修復関数
  PLAN_OR_REQUIREMENTS: docs/plans/deployment-plan.md の Task 2
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: verifyIndex() と repairIndex() を追加
```

## ワークフロー連携

**Subagent-Driven Development:**
- 各タスク後にレビュー
- 問題の複利化を防ぐ

**Executing Plans:**
- 各バッチ（3タスク）後にレビュー

**Ad-Hoc Development:**
- マージ前
- 行き詰まり時

## 危険信号

**Never:**
- 「簡単だから」でレビュー省略
- Critical を無視
- Important 未修正で進行
- 妥当な指摘に感情的反論

**レビュアーが誤っている場合:**
- 技術的根拠で反論
- コード/テストで裏付け
- 必要なら明確化を依頼

テンプレート: `requesting-code-review/code-reviewer.md`
