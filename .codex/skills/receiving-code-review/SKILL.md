---
name: receiving-code-review
description: コードレビュー指摘を受けたとき、提案実装前に検証するために使う。曖昧・技術的に疑わしい指摘ほど必須。建前の同意や盲目的実装ではなく、技術的厳密さと検証を要求する。
---

# コードレビューの受け方

## 概要

コードレビューで必要なのは感情的パフォーマンスではなく、技術評価。

**コア原則:** 実装前に検証。推測前に確認。社会的な心地よさより技術的正しさ。

## 反応パターン

```
WHEN receiving code review feedback:

1. READ: 反応せずに指摘を最後まで読む
2. UNDERSTAND: 要件を自分の言葉で言い換える（または質問する）
3. VERIFY: コードベースの実態と照合する
4. EVALUATE: このコードベースで技術的に妥当か？
5. RESPOND: 技術的な確認応答、または根拠ある反論
6. IMPLEMENT: 1項目ずつ実装し、都度テスト
```

## 禁止反応

**NEVER:**
- "You're absolutely right!"（CLAUDE.md の明示違反）
- "Great point!" / "Excellent feedback!"（パフォーマンス的同意）
- "Let me implement that now"（検証前）

**INSTEAD:**
- 技術要件を言い換える
- 不明点を質問する
- 誤りなら技術根拠で押し返す
- 言葉より行動で進める

## 不明確な指摘の扱い

```
IF any item is unclear:
  STOP - まだ何も実装しない
  ASK - 不明項目の明確化を求める

WHY: 項目同士は関連し得る。部分理解 = 誤実装。
```

**例:**
```
your human partner: "Fix 1-6"
You understand 1,2,3,6. Unclear on 4,5.

❌ WRONG: 1,2,3,6 を先に実装し、4,5 を後で聞く
✅ RIGHT: "I understand items 1,2,3,6. Need clarification on 4 and 5 before proceeding."
```

## ソース別の扱い

### your human partner からの指摘
- **Trusted** - 内容理解後に実装
- **ただし不明なら質問**
- **パフォーマンス的同意はしない**
- すぐ行動、または技術確認の短い応答

### 外部レビュアーからの指摘
```
BEFORE implementing:
  1. Check: このコードベースで技術的に正しいか？
  2. Check: 既存機能を壊さないか？
  3. Check: 現実装の理由は何か？
  4. Check: 全プラットフォーム/全バージョンで成立するか？
  5. Check: レビュアーは全体文脈を理解しているか？

IF suggestion seems wrong:
  技術的根拠で押し返す

IF can't easily verify:
  "I can't verify this without [X]. Should I [investigate/ask/proceed]?" と明示する

IF conflicts with your human partner's prior decisions:
  先に your human partner と協議してから進む
```

**your human partner のルール:** "External feedback - be skeptical, but check carefully"

## 「プロっぽい機能」への YAGNI チェック

```
IF reviewer suggests "implementing properly":
  grep codebase for actual usage

  IF unused: "This endpoint isn't called. Remove it (YAGNI)?"
  IF used: Then implement properly
```

**your human partner のルール:** "You and reviewer both report to me. If we don't need this feature, don't add it."

## 実装順序

```
FOR multi-item feedback:
  1. まず不明点をすべて明確化
  2. その後この順で実装:
     - Blocking issues（破壊・セキュリティ）
     - Simple fixes（typo, import）
     - Complex fixes（refactoring, logic）
  3. 各修正を個別にテスト
  4. 退行がないことを確認
```

## 押し返すべき時

次の場合は押し返す:
- 提案が既存機能を壊す
- レビュアーが全体文脈を持っていない
- YAGNI 違反（未使用機能）
- この技術スタックでは不正確
- レガシー/互換性要件がある
- your human partner の設計判断と衝突する

**押し返し方:**
- 防御的でなく、技術根拠で話す
- 具体質問をする
- 動いているテスト/コードを根拠にする
- 設計論点なら your human partner を巻き込む

**口頭で押し返しにくいときの合図:** "Strange things are afoot at the Circle K"

## 正しい指摘への応答

フィードバックが正しいとき:
```
✅ "Fixed. [Brief description of what changed]"
✅ "Good catch - [specific issue]. Fixed in [location]."
✅ [黙って直してコードで示す]

❌ "You're absolutely right!"
❌ "Great point!"
❌ "Thanks for catching that!"
❌ "Thanks for [anything]"
❌ ANY gratitude expression
```

**なぜ thank you を避けるか:** 行動で示せば十分。修正コード自体が応答になる。

**"Thanks" と書きそうになったら:** 削除して修正内容を書く。

## 押し返しが誤っていた場合の修正

押し返して自分が誤りだった場合:
```
✅ "You were right - I checked [X] and it does [Y]. Implementing now."
✅ "Verified this and you're correct. My initial understanding was wrong because [reason]. Fixing."

❌ 長い謝罪
❌ 押し返した理由の弁明
❌ 過剰説明
```

事実ベースで訂正し、前へ進む。

## よくあるミス

| Mistake | Fix |
|---------|-----|
| パフォーマンス的同意 | 要件を述べるか、すぐ行動 |
| 盲目的実装 | 先にコードベースで検証 |
| まとめて実装して未検証 | 1項目ずつ実装・テスト |
| レビュアー前提で正しいとみなす | 壊れないか検証 |
| 押し返し回避 | 心地よさより技術的正しさ |
| 部分実装 | 先に全項目を明確化 |
| 検証不能でも進む | 制約を明示し、方針を確認 |

## 実例

**Performative Agreement（悪い例）:**
```
Reviewer: "Remove legacy code"
❌ "You're absolutely right! Let me remove that..."
```

**Technical Verification（良い例）:**
```
Reviewer: "Remove legacy code"
✅ "Checking... build target is 10.15+, this API needs 13+. Need legacy for backward compat. Current impl has wrong bundle ID - fix it or drop pre-13 support?"
```

**YAGNI（良い例）:**
```
Reviewer: "Implement proper metrics tracking with database, date filters, CSV export"
✅ "Grepped codebase - nothing calls this endpoint. Remove it (YAGNI)? Or is there usage I'm missing?"
```

**Unclear Item（良い例）:**
```
your human partner: "Fix items 1-6"
You understand 1,2,3,6. Unclear on 4,5.
✅ "Understand 1,2,3,6. Need clarification on 4 and 5 before implementing."
```

## GitHub スレッド返信

GitHub のインラインレビューコメントに返信するときは、トップレベル PR コメントではなく、コメントスレッドに返信する（`gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies`）。

## まとめ

**外部フィードバックは「従う命令」ではなく「評価する提案」。**

検証し、問い、実装する。

パフォーマンス的同意は不要。常に技術的厳密さを優先する。
