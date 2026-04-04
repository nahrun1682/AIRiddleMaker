---
name: verification-before-completion
description: 作業完了・修正完了・テスト成功を主張する直前（コミット/PR作成前）に使う。成功主張の前に検証コマンドを実行し、出力確認を必須化する。常に「主張より証拠」。
---

# 完了主張前の検証

## 概要

検証なしで「完了」を主張するのは、効率化ではなく不誠実である。

**中核原則:** 常に「主張より証拠」。

**このルールの文言だけを守って精神を破るのも違反である。**

## 鉄則

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

このメッセージ内で検証コマンドを実行していないなら、成功を主張してはならない。

## ゲート関数

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## よくある失敗

| 主張 | 必要な証拠 | 不十分なもの |
|-------|----------|----------------|
| テスト成功 | テスト出力: 失敗 0 件 | 以前の実行結果、「通るはず」 |
| Lint クリア | Linter 出力: エラー 0 件 | 部分チェック、推測 |
| ビルド成功 | ビルドコマンド: exit 0 | Lint 成功、ログの見た目 |
| バグ修正済み | 元症状のテスト: 成功 | コード変更済み、直った想定 |
| 回帰テスト有効 | Red-Green サイクル確認済み | 1回だけ通ったテスト |
| エージェント完了 | VCS 差分で変更を確認 | エージェントの「成功」報告 |
| 要件達成 | 要件を行単位でチェック | テスト成功のみ |

## 危険信号 - 停止

- 「should」「probably」「seems to」など推測語を使っている
- 検証前に満足表現を出しそう（"Great!", "Perfect!", "Done!" など）
- 検証なしで commit/push/PR しようとしている
- エージェントの成功報告を信じ切っている
- 部分検証に依存している
- 「今回だけは」と思っている
- 疲れて早く終わらせたくなっている
- **検証未実行なのに成功を示唆するあらゆる表現**

## 合理化の防止

| 言い訳 | 現実 |
|--------|---------|
| 「もう動くはず」 | 検証を実行する |
| 「自信がある」 | 自信 ≠ 証拠 |
| 「今回だけ」 | 例外なし |
| 「Lint は通った」 | Lint ≠ コンパイル |
| 「エージェントが成功と言った」 | 独立に検証する |
| 「疲れている」 | 疲労は免責にならない |
| 「部分チェックで十分」 | 部分確認では証明にならない |
| 「言い方を変えれば対象外」 | 文言より精神 |

## 重要パターン

**テスト:**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**回帰テスト（TDD Red-Green）:**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**ビルド:**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "Linter passed" (linter doesn't check compilation)
```

**要件:**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, phase complete"
```

**エージェント委譲:**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Trust agent report
```

## なぜ重要か

24件の失敗記録より:
- 人間パートナーに「信じられない」と言われ、信頼が毀損した
- 未定義関数が出荷され、実行時クラッシュの恐れがあった
- 要件未達のまま出荷され、機能が不完全だった
- 誤った完了報告で手戻りが発生した
- 「誠実さは中核価値。嘘をつけば置き換えられる」に反する

## 適用タイミング

**常に以下の前で適用:**
- あらゆる成功・完了主張
- あらゆる満足表現
- 作業状態を肯定するあらゆる発言
- コミット、PR作成、タスク完了
- 次タスクへの移動
- エージェントへの委譲

**このルールが適用される対象:**
- 完全一致の定型句
- 言い換えや同義語
- 成功を示唆する含意
- 完了・正しさを示すあらゆるコミュニケーション

## 結論

**検証の近道はない。**

コマンドを実行し、出力を読み、その後に結果を主張する。

これは交渉不可である。
