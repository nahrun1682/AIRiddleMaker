"""Scorer MCP server — FastAPI + fastapi_mcp で採点ツールを MCP 公開する."""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from openai import OpenAI
from pydantic import BaseModel, Field

_PROMPT_PATH = Path(__file__).parent / "scorer_prompt.md"
_openai_client: OpenAI | None = None
_scorer_model: str = "gpt-5.4"


class ScoreRequest(BaseModel):
    question: str = Field(..., min_length=1, description="なぞなぞ問題文")
    answer: str = Field(..., min_length=1, description="なぞなぞの答え")


class ScoreResponse(BaseModel):
    uniqueness: bool
    structural_soundness: bool
    concrete_grounding: bool
    strict_score: float = Field(ge=0.0, le=10.0)
    passed: bool
    reason: str | None = None
    strict_review: str | None = None


def _load_system_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def create_app(model: str = "gpt-5.4", api_key: str | None = None) -> FastAPI:
    global _openai_client, _scorer_model
    _scorer_model = model

    if api_key:
        _openai_client = OpenAI(api_key=api_key)
    else:
        _openai_client = OpenAI()

    app = FastAPI(
        title="Riddle Scorer",
        description="日本語なぞなぞ採点 MCP サーバー",
    )

    @app.post("/score", response_model=ScoreResponse, operation_id="score_riddle")
    def score_riddle(req: ScoreRequest) -> ScoreResponse:
        """なぞなぞを採点し、スコアと合否を返す。"""
        system_prompt = _load_system_prompt()
        user_prompt = f"問題文: {req.question}\n答え: {req.answer}"

        response = _openai_client.chat.completions.create(
            model=_scorer_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)
        return ScoreResponse(**data)

    mcp = FastApiMCP(app)
    mcp.mount_http()

    return app


def main() -> None:
    import argparse
    import os

    from riddle.config import load_riddle_config

    parser = argparse.ArgumentParser(description="Scorer MCP Server")
    parser.add_argument("--port", type=int, help="ポート番号")
    parser.add_argument("--model", type=str, help="採点モデル")
    args = parser.parse_args()

    config_path = Path(os.getenv("RIDDLE_CONFIG_FILE", "riddle.toml"))
    config = load_riddle_config(config_path)

    port = args.port or config.scorer_port
    model = args.model or config.scorer_model

    dotenv_path = Path(__file__).parent.parent.parent / ".env"
    if dotenv_path.is_file():
        for line in dotenv_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

    import uvicorn

    app = create_app(model=model)
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
