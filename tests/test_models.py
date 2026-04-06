import pytest
from pydantic import ValidationError
from riddle.models import RiddleResult, ScoreDetail


def test_riddle_result_valid():
    result = RiddleResult(
        question="食べるほど減るのに、食べないと増えるものは？",
        answer="食欲",
        pattern="paradox",
        score=ScoreDetail(uniqueness=True, single_paradox=True, observation_based=True),
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
        "score": {"uniqueness": true, "single_paradox": false, "observation_based": true},
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
            score=ScoreDetail(uniqueness=True, single_paradox=True, observation_based=True),
            attempts=0,
        )


def test_score_detail_passed_all_true():
    score = ScoreDetail(uniqueness=True, single_paradox=True, observation_based=True)
    assert score.passed is True


def test_score_detail_passed_any_false():
    score = ScoreDetail(uniqueness=True, single_paradox=False, observation_based=True)
    assert score.passed is False
