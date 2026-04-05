# AIRiddleMaker

AOF（Adaptive Originality Filtering）に基づく、多言語なぞなぞ生成の研究実装プロジェクトです。  
対象論文: `arXiv:2508.18709v3`  
目的: 「使える生成ツール」と「論文再現実験」を同時に満たすこと。

## 5分クイックスタート

> 現在は実装準備段階です。以下は README 先行の実行インターフェース仕様です。

```bash
# 1) 環境構築
uv venv
source .venv/bin/activate
uv sync --extra dev

# 2) （予定）最小実行
uv run python -m airiddlemaker.cli generate \
  --answer "影" \
  --lang ja \
  --theta 0.75 \
  --max-retries 8
```

想定出力:
- 生成なぞなぞ本文
- 採用/棄却ログ（類似度）
- 最終スコア（任意で RiddleScore）

## 使い方（予定 CLI/API）

### 主要オプション
- `--answer`: 先に固定する答え（Answer-First）
- `--lang`: 生成言語（`en|ja|zh|fr|ar`）
- `--theta`: 類似度しきい値（既定 `0.75`）
- `--max-retries`: 棄却後の再試行回数 `k`
- `--temperature`: 生成温度（既定 `0.7`）
- `--n-candidates`: 1回で出す候補数

### ユースケース
1. 単発生成（答え固定）
2. 複数候補生成して最良を採用
3. 指標付きで品質比較（Self-BLEU/Distinct-2/RiddleScore）

## 論文手法詳細（AOF）

### 1) AOF の基本ループ
1. 答えを固定して候補なぞなぞを生成  
2. 参照集合（既存なぞなぞ）との意味類似度を計算  
3. 類似度が高すぎる候補を棄却  
4. 採用条件を満たすまで再生成（最大 `k` 回）

### 2) 意味類似フィルタ
- 埋め込み: MiniLM 系
- 類似度: cosine similarity
- 判定: `max_sim > theta` なら棄却（既定 `theta = 0.75`）

### 3) 棄却サンプリング
擬似コード:

```text
for t in 1..k:
  c = generate(answer, lang, constraints)
  s = max_cosine_similarity(c, reference_pool)
  if s <= theta:
    return c
return best_candidate_seen
```

### 4) RiddleScore
GitHub 表示互換のため、式はプレーン記法で示します。

`RiddleScore = alpha*Novelty + beta*Diversity + gamma*Fluency + delta*Alignment`

- `Novelty`: 参照集合との意味距離（MiniLM）
- `Diversity`: Distinct-2
- `Fluency`: 逆 perplexity（論文では GPT-2.5 系）
- `Alignment`: なぞなぞ文と答えの意味整合（BERTScore）

重み（論文準拠）:
- `alpha = 0.30`
- `beta = 0.20`
- `gamma = 0.30`
- `delta = 0.20`

### 5) 閾値感度（運用上の注意）
- `theta` が低すぎる: 生成失敗率が上がる
- `theta` が高すぎる: テンプレ流用が増える
- 論文では `0.75` がバランス点

## 論文再現ガイド（予定）

### 再現対象
- 比較手法: Zero-shot / Few-shot / CoT / Adversarial / AOF
- モデル: GPT-4o / LLaMA 3.1 / DeepSeek R1
- 言語: `en, ja, zh, fr, ar`

### 主要評価
- Self-BLEU（重複）
- Distinct-2（語彙多様性）
- RiddleScore（複合）
- 人手評価（流暢性・新規性・文化適合・解答可能性）

## 実装方針（論文準拠 vs 実装簡略化）

### 論文準拠で守る点
- AOF ループ
- `theta=0.75` デフォルト
- RiddleScore の4成分と重み
- Answer-First 生成

### 実装で簡略化しうる点
- バックエンドモデル差（利用可能な埋め込み/LMへ置換）
- データセットの縮小版利用
- 人手評価は別途スクリプト化

## 開発

```bash
uv run pytest
uv run black --check .
uv run isort --check-only .
uv run flake8
uv run mypy src/
```

## 制約と倫理

- 文化的バイアスは残る可能性があります。
- 既存なぞなぞとの近似は完全には防げません。
- 高リスク用途（教育評価・心理評価・法的文脈など）での自動利用は非推奨です。

## 参考

- 論文 PDF: `docs/paper/AOF/2508.18709v3.pdf`
- 日本語訳: `docs/paper/AOF/2508.18709v3_ja.md`
