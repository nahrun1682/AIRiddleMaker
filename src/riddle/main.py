import argparse
import sys

from riddle.service import RiddleService


def main(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="日本語なぞなぞ生成システム")
    parser.add_argument("--pattern", help="生成パターン (paradox/pun/char_extract 等)")
    parsed = parser.parse_args(args)

    theme = input("テーマを入力してください（例: 食べ物、動物、季節）: ").strip() or None

    service = RiddleService()
    try:
        result = service.generate_riddle(pattern=parsed.pattern, theme=theme)
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


if __name__ == "__main__":
    main()
