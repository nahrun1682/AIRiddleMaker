---
name: gguf-quantization
description: GGUF 形式と llama.cpp 量子化を使って CPU/GPU 推論を効率化するときに使う。民生ハードウェア、Apple Silicon、2〜8bit の柔軟量子化が必要な状況で適用。
version: 1.0.0
author: Orchestra Research
license: MIT
tags: [GGUF, Quantization, llama.cpp, CPU Inference, Apple Silicon, Model Compression, Optimization]
dependencies: [llama-cpp-python>=0.2.0]
---

# GGUF - llama.cpp 向け量子化フォーマット

GGUF（GPT-Generated Unified Format）は llama.cpp の標準モデル形式。CPU、Apple Silicon、GPU での効率的推論を可能にし、2〜8bit の柔軟な量子化を提供する。

## GGUF を使う場面

**適用条件:**
- ノートPCやデスクトップなど民生ハードウェアで運用
- Apple Silicon（M1/M2/M3）で Metal を活用
- GPU 必須にせず CPU 推論したい
- Q2_K〜Q8_0 の量子化を選びたい
- LM Studio / Ollama / text-generation-webui などローカル推論ツールを使う

**主な利点:**
- CPU、Apple Silicon、NVIDIA、AMD に広く対応
- Python ランタイム非依存の C/C++ 推論が可能
- K-quant を含む幅広い量子化方式
- エコシステム対応が広い
- imatrix（重要度行列）で低bit品質を改善可能

**代替を使うべき場合:**
- NVIDIA 上で精度最優先: AWQ / GPTQ
- HuggingFace で高速かつ簡易: HQQ
- transformers と統合重視: bitsandbytes
- NVIDIA 本番最速重視: TensorRT-LLM

## クイックスタート

### インストール

```bash
# llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build --config Release

# Python バインディング（任意）
pip install llama-cpp-python
```

### 推論例

```bash
./build/bin/llama-cli -m model.gguf -p "Hello" -n 128
```

### 量子化例

```bash
# FP16 モデルを Q4_K_M に量子化
./build/bin/llama-quantize model-f16.gguf model-q4_k_m.gguf q4_k_m
```

## 量子化方式の目安

| 方式 | サイズ削減 | 速度 | 品質 |
|------|------------|------|------|
| Q8_0 | 小 | 中 | 高 |
| Q6_K | 中 | 中〜高 | 高 |
| Q5_K_M | 中〜大 | 高 | 中〜高 |
| Q4_K_M | 大 | 高 | 中 |
| Q3_K_M | かなり大 | 非常に高 | 中〜低 |
| Q2_K | 最大 | 最速 | 低 |

## 選定ガイド

- **品質重視:** Q8_0 / Q6_K
- **バランス重視:** Q5_K_M / Q4_K_M
- **メモリ最小化:** Q3_K_M / Q2_K
- **Apple Silicon:** Q4_K_M か Q5_K_M から開始
- **CPUのみ:** Q4_K_M 〜 Q6_K が実用帯

## 変換と検証の流れ

1. 元モデル（FP16 など）を GGUF 化
2. 目的に応じた量子化方式を選択
3. 推論品質（困難プロンプト）と速度を測定
4. メモリ使用量を確認
5. 目標 SLA に合わせて再選定

## ベンチマーク項目

- tokens/sec（生成速度）
- first token latency（初回遅延）
- peak RAM / VRAM
- 長文・難問での品質劣化
- 温度/コンテキスト長変更時の安定性

## よくある失敗

- 目的不明のまま量子化方式を選ぶ
- 速度だけ見て品質評価しない
- コンテキスト長を揃えず比較する
- 推論設定（temp/top_p/repeat_penalty）を統一せず比較
- 運用環境と異なるマシンでだけ評価する

## 実装上の注意

- 量子化比較時は同一プロンプト・同一 seed・同一設定で測る
- 低bit化するほど hallucination と事実誤認が増えやすい
- 本番投入前に難ケース回帰テストを必ず回す
- 速度改善より安定品質を優先する用途では Q5 以上を基準にする

## 推奨運用

1. 候補を Q4_K_M / Q5_K_M / Q6_K の3本で作る
2. 品質閾値を満たす最小サイズを選ぶ
3. モデル更新時は同じ評価セットで再比較
4. 推論ログと失敗ケースを継続収集し再チューニング
