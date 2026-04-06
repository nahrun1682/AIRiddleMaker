import argparse
import os
import sys
from pathlib import Path

from riddle.config import load_riddle_config
from riddle.service import RiddleService


def main(args: list[str] | None = None) -> None:
    config_path = Path(os.getenv("RIDDLE_CONFIG_FILE", "riddle.toml"))
    config = load_riddle_config(config_path)

    parser = argparse.ArgumentParser(description="日本語なぞなぞ生成システム")
    parser.add_argument("--pattern", help="生成パターン (paradox/pun/char_extract 等)")
    parser.add_argument(
        "--max-retries",
        type=int,
        default=config.max_retries,
        help=f"生成ループ上限回数（デフォルト: {config.max_retries}）",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Codexセッションイベントをリアルタイム表示する",
    )
    parsed = parser.parse_args(args)

    theme = input("テーマを入力してください（例: 食べ物、動物、季節）: ").strip() or None

    service = RiddleService()
    try:
        result = service.generate_riddle(
            pattern=parsed.pattern,
            theme=theme,
            max_retries=parsed.max_retries,
            trace=parsed.trace or config.trace_default,
            model=config.model,
            reasoning_effort=config.reasoning_effort,
            strict_threshold=config.strict_threshold,
            require_reason_fields=config.require_reason_fields,
            scorer_port=config.scorer_port,
            scorer_model=config.scorer_model,
        )
    except RuntimeError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nテーマ: {theme or '指定なし'}")
    print(f"問題: {result.question}")
    print(f"答え: {result.answer}")
    print(f"パターン: {result.pattern}")
    print(f"試行回数: {result.attempts}回")
    print(
        f"採点: 一意性={result.score.uniqueness} / "
        f"一現象一逆説={result.score.single_paradox} / "
        f"観察ベース={result.score.observation_based}"
    )
    print(f"厳格スコア: {result.score.strict_score}")
    print(f"判定: passed={result.score.passed}")
    if result.score.reason:
        print(f"判定理由: {result.score.reason}")
    if result.score.strict_review:
        print("講評:")
        print(result.score.strict_review)


if __name__ == "__main__":
    main()
