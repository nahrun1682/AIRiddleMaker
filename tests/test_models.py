import pytest
from pydantic import ValidationError
from riddle.models import RiddleResult, ScoreDetail


def test_riddle_result_valid():
    result = RiddleResult(
        question="食べるほど減るのに、食べないと増えるものは？",
        answer="食欲",
        pattern="paradox",
        score=ScoreDetail(
            uniqueness=True,
            structural_soundness=True,
            concrete_grounding=True,
            strict_score=9.6,
            passed=True,
        ),
        attempts=2,
    )
    assert result.question == "食べるほど減るのに、食べないと増えるものは？"
    assert result.attempts == 2
    assert result.score.uniqueness is True


def test_riddle_result_from_json():
    json_str = """{
        "question": "テスト問題",
        "answer": "テスト答え",
        "pattern": "pun",
        "score": {
            "uniqueness": true,
            "structural_soundness": false,
            "concrete_grounding": true,
            "strict_score": 7.2,
            "passed": false
        },
        "attempts": 1
    }"""
    result = RiddleResult.model_validate_json(json_str)
    assert result.pattern == "pun"


def test_riddle_result_invalid_attempts():
    with pytest.raises(ValidationError):
        RiddleResult(
            question="q",
            answer="a",
            pattern="pun",
            score=ScoreDetail(
                uniqueness=True,
                structural_soundness=True,
                concrete_grounding=True,
                strict_score=9.6,
                passed=True,
            ),
            attempts=0,
        )


def test_score_detail_accepts_pass_when_all_conditions_met():
    score = ScoreDetail(
        uniqueness=True,
        structural_soundness=True,
        concrete_grounding=True,
        strict_score=6.0,
        passed=True,
        reason="妥当",
        strict_review="厳しく評価：6.0/10点（合格）",
    )
    assert score.passed is True
    assert score.reason == "妥当"
    assert "厳しく評価" in score.strict_review


def test_score_detail_requires_strict_score_and_passed():
    with pytest.raises(ValidationError):
        ScoreDetail(uniqueness=True, structural_soundness=True, concrete_grounding=True)


def test_score_detail_rejects_inconsistent_passed():
    with pytest.raises(ValidationError):
        ScoreDetail(
            uniqueness=True,
            structural_soundness=False,
            concrete_grounding=True,
            strict_score=6.9,
            passed=True,
        )
