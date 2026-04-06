from pydantic import BaseModel, Field, model_validator


class ScoreDetail(BaseModel):
    uniqueness: bool
    single_paradox: bool
    observation_based: bool
    strict_score: float = Field(ge=0.0, le=10.0)
    passed: bool
    reason: str | None = None
    strict_review: str | None = None

    @model_validator(mode="after")
    def validate_passed_consistency(self) -> "ScoreDetail":
        expected_passed = (
            self.uniqueness
            and self.single_paradox
            and self.observation_based
            and self.strict_score >= 9.5
        )
        if self.passed != expected_passed:
            raise ValueError(
                "passed must match uniqueness/single_paradox/observation_based "
                "and strict_score >= 9.5"
            )
        return self


class RiddleResult(BaseModel):
    question: str
    answer: str
    pattern: str
    score: ScoreDetail
    attempts: int = Field(ge=1)
