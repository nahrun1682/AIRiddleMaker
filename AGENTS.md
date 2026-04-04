# AGENTS.md

このファイルは、Codex がこのリポジトリで作業する際のガイドラインです。

## プロジェクト概要

このリポジトリは、モダンな Python 開発向けに最適化されたプロジェクトです。  
業界標準のツールと、スケーラブルなアプリケーション開発のベストプラクティスを前提とします。

## 開発コマンド

### 環境管理
- `uv venv` - 仮想環境（`.venv`）を作成
- `source .venv/bin/activate`（Linux/Mac）または `.venv\Scripts\activate`（Windows） - 仮想環境を有効化
- `deactivate` - 仮想環境を無効化
- `uv sync` - `pyproject.toml` / `uv.lock` から依存関係を同期
- `uv sync --extra dev` - 開発用依存関係を含めて同期

### パッケージ管理
- `uv add <package>` - 本番依存を追加
- `uv add --dev <package>` - 開発依存を追加
- `uv remove <package>` - 依存を削除
- `uv lock` - ロックファイルを再生成

### テスト実行
- `uv run pytest` - すべてのテストを実行
- `uv run pytest -v` - 詳細表示で実行
- `uv run pytest --cov` - カバレッジ付きで実行
- `uv run pytest --cov-report=html` - HTML カバレッジレポート生成
- `uv run pytest -x` - 最初の失敗で停止
- `uv run pytest -k "test_name"` - 名前パターンでテストを絞り込み
- `uv run python -m unittest` - unittest で実行

### コード品質
- `uv run black .` - Black で整形
- `uv run black --check .` - 整形差分のみ確認
- `uv run isort .` - import を整列
- `uv run isort --check-only .` - import 整列の確認のみ
- `uv run flake8` - Flake8 で lint
- `uv run pylint src/` - Pylint で lint
- `uv run mypy src/` - MyPy で型チェック

### 開発補助
- `uv lock --upgrade` - 依存を更新してロックを再生成
- `uv run python -c "import sys; print(sys.version)"` - Python バージョン確認
- `uv run python -m site` - site 情報を表示
- `uv run python -m pdb script.py` - pdb デバッグ

## 技術スタック

### コア技術
- **Python** - 主言語（3.13+）
- **uv** - 依存管理と仮想環境管理

### よく使うフレームワーク
- **Django** - 高機能 Web フレームワーク
- **Flask** - 軽量 Web フレームワーク
- **FastAPI** - 自動ドキュメント生成を備えた API フレームワーク
- **SQLAlchemy** - SQL ツールキット / ORM
- **Pydantic** - 型ヒントを利用したデータ検証

### データサイエンス / ML
- **NumPy**
- **Pandas**
- **Matplotlib/Seaborn**
- **Scikit-learn**
- **TensorFlow/PyTorch**

### テスト関連
- **pytest**
- **unittest**
- **pytest-cov**
- **factory-boy**
- **responses**

### コード品質ツール
- **Black**
- **isort**
- **flake8**
- **pylint**
- **mypy**
- **pre-commit**

## プロジェクト構成ガイド

### ファイル構成
```text
src/
├── package_name/
│   ├── __init__.py
│   ├── main.py          # アプリケーションエントリーポイント
│   ├── models/          # データモデル
│   ├── views/           # Web ビュー（Django/Flask）
│   ├── api/             # API エンドポイント
│   ├── services/        # ビジネスロジック
│   ├── utils/           # ユーティリティ関数
│   └── config/          # 設定ファイル
tests/
├── __init__.py
├── conftest.py          # pytest 設定
├── test_models.py
├── test_views.py
└── test_utils.py
pyproject.toml           # プロジェクト定義と依存関係
uv.lock                  # 解決済み依存のロックファイル
```

### 命名規則
- **ファイル / モジュール**: snake_case（`user_profile.py`）
- **クラス**: PascalCase（`UserProfile`）
- **関数 / 変数**: snake_case（`get_user_data`）
- **定数**: UPPER_SNAKE_CASE（`API_BASE_URL`）
- **プライベートメソッド**: 先頭に `_`（`_private_method`）

## Python ガイドライン

### 型ヒント
- 関数の引数と戻り値に型ヒントを付ける
- 必要に応じて `typing` から型を import する
- nullable は `Optional` を使う
- 複数型は `Union` を使う
- 複雑な型はコメントで補足する

### コーディングスタイル
- PEP 8 に従う
- 変数名・関数名は意味が伝わるものを使う
- 関数は単一責務を維持する
- モジュール / クラス / 関数には docstring を付ける
- 1行 88 文字（Black デフォルト）を目安にする

### ベストプラクティス
- 単純な変換には内包表記を使う
- パス操作は `os.path` より `pathlib` を優先する
- リソース管理はコンテキストマネージャ（`with`）を使う
- 例外は `try/except` で適切に処理する
- `print` ではなく `logging` を使う

## テスト基準

### テスト構造
- ソース構造に対応する形でテストを配置する
- 期待する振る舞いが分かるテスト名を付ける
- AAA パターン（Arrange, Act, Assert）に従う
- 共通データは fixture を使う
- 関連テストはクラス単位で整理する

### カバレッジ目標
- 90%以上を目標にする
- ビジネスロジックにはユニットテストを書く
- 外部依存は統合テストで検証する
- 外部サービスはモック化する
- エラー系と境界ケースもテストする

### pytest 設定例
```python
# pytest.ini または pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=term-missing"
```

## UV 環境セットアップ

### 作成と有効化
```bash
# 仮想環境の作成
uv venv

# 有効化（Linux/Mac）
source .venv/bin/activate

# 有効化（Windows）
.venv\Scripts\activate

# 依存関係の同期
uv sync
uv sync --extra dev
```

### 依存管理方針
- 依存関係の正本は `pyproject.toml`
- 再現性の担保は `uv.lock`
- 依存追加は `uv add` / `uv add --dev`
- ロック更新は `uv lock`

## Django 向けガイド

### 構成例
```text
project_name/
├── manage.py
├── project_name/
│   ├── __init__.py
│   ├── settings/
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── users/
│   ├── products/
│   └── orders/
├── pyproject.toml
└── uv.lock
```

### よく使うコマンド
- `uv run python manage.py runserver` - 開発サーバー起動
- `uv run python manage.py migrate` - マイグレーション適用
- `uv run python manage.py makemigrations` - マイグレーション作成
- `uv run python manage.py createsuperuser` - 管理ユーザー作成
- `uv run python manage.py collectstatic` - 静的ファイル収集
- `uv run python manage.py test` - Django テスト実行

## FastAPI 向けガイド

### 構成例
```text
src/
├── main.py
├── api/
│   ├── __init__.py
│   ├── dependencies.py
│   └── v1/
│       ├── __init__.py
│       └── endpoints/
├── core/
│   ├── __init__.py
│   ├── config.py
│   └── security.py
├── models/
├── schemas/
└── services/
```

### よく使うコマンド
- `uv run uvicorn main:app --reload` - 開発サーバー起動
- `uv run uvicorn main:app --host 0.0.0.0 --port 8000` - 本番向け起動

## セキュリティガイド

### 依存関係
- `uv lock --upgrade` で定期的に依存更新を確認する
- `uvx pip-audit` で既知脆弱性を確認する
- 依存バージョンは `uv.lock` で固定する
- 仮想環境を使って依存を分離する

### コードセキュリティ
- Pydantic などで入力を検証する
- 秘密情報は環境変数で管理する
- 適切な認証・認可を実装する
- DB 操作前にデータを適切にサニタイズする
- 本番環境では HTTPS を使う

## 開発ワークフロー

### 開始前
1. Python バージョン互換を確認する
2. 仮想環境を作成して有効化する
3. `uv sync` で依存関係を同期する
4. `uv run mypy` で型チェックを実行する

### 開発中
1. 型ヒントを活用する
2. こまめにテストを実行する
3. 意味のあるコミットメッセージを使う
4. コミット前に Black で整形する

### コミット前
1. テスト一式を実行: `uv run pytest`
2. 整形チェック: `uv run black --check .`
3. import 整列チェック: `uv run isort --check-only .`
4. lint 実行: `uv run flake8`
5. 型チェック: `uv run mypy src/`
