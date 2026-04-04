---
name: docs-search
description: 自動生成されたコードベース文書（関数シグネチャ、API仕様、クラス定義、コメント）を検索するときに使う。ユーザーが「docs を検索して」「ドキュメントを探して」「関数を確認して」「API を確認して」と依頼した場合や、実装前に正しいシグネチャとパターンを検証する場合に適用。
---

# AI Maestro ドキュメント検索

関数シグネチャ、クラス定義、API ドキュメント、コードコメントのために、コードベースの自動生成ドキュメントを検索する。コードを書く前に正しいパターンを検証する。[AI Maestro](https://github.com/23blocks-OS/ai-maestro) スイートの一部。

## 前提条件

ドキュメントがインデックス済みの [AI Maestro](https://github.com/23blocks-OS/ai-maestro) がローカルで動作している必要がある。

```bash
# ドキュメントツールをインストール
git clone https://github.com/23blocks-OS/ai-maestro-plugins.git
cd ai-maestro-plugins && ./install-doc-tools.sh
```

## コア挙動

コード変更を実装する前に、必ず先に docs を検索する:

```
指示を受ける -> docs 検索 -> その後に実装
```

## コマンド

### Search
| Command | Description |
|---------|-------------|
| `docs-search.sh <query>` | セマンティックなドキュメント検索 |
| `docs-search.sh --keyword <term>` | 正確なキーワード一致 |
| `docs-find-by-type.sh <type>` | タイプ別検索（function, class, module） |
| `docs-get.sh <doc-id>` | ドキュメント全文を取得 |

### Index
| Command | Description |
|---------|-------------|
| `docs-index.sh [path]` | プロジェクト全体をフルインデックス |
| `docs-index-delta.sh [path]` | 差分インデックス（新規/変更ファイルのみ） |
| `docs-list.sh` | インデックス済みドキュメント一覧 |
| `docs-stats.sh` | インデックス統計 |

## ドキュメントタイプ

| Type | Sources |
|------|---------|
| `function` | JSDoc, RDoc, docstrings |
| `class` | クラスレベルコメント |
| `module` | モジュール/名前空間コメント |
| `interface` | TypeScript interface |
| `component` | React/Vue コンポーネントコメント |
| `readme` | README ファイル |
| `guide` | docs/ フォルダの内容 |

## 利用例

```bash
# セマンティック検索
docs-search.sh "authentication flow"

# 特定識別子をキーワード検索
docs-search.sh --keyword "UserController"

# クラス文書を全件検索
docs-find-by-type.sh class

# ドキュメント詳細を全文取得
docs-get.sh doc-abc123

# 初回インデックス
docs-index.sh /path/to/project

# 変更後に差分更新
docs-index-delta.sh
```

## AI Maestro 全体像

このスキルは [AI Maestro](https://github.com/23blocks-OS/ai-maestro) プラットフォームの一部で、AI エージェントオーケストレーション向けに **6 つのスキル**（messaging, memory, docs, graph, planning, agent management）を提供する。
