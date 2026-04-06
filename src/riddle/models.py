from pydantic import BaseModel, Field, model_validator


class ScoreDetail(BaseModel):
    uniqueness: bool
    structural_soundness: bool
    concrete_grounding: bool
    strict_score: float = Field(ge=0.0, le=10.0)
    passed: bool
    reason: str | None = None
    strict_review: str | None = None

    @model_validator(mode="after")
    def validate_passed_consistency(self) -> "ScoreDetail":
        expected_passed = (
            self.structural_soundness
            and self.concrete_grounding
            and self.strict_score >= 6.0
        )
        if self.passed != expected_passed:
            raise ValueError(
                "passed must match structural_soundness/concrete_grounding "
                "and strict_score >= 6.0"
            )
        return self


class RiddleResult(BaseModel):
    question: str
    answer: str
    pattern: str
    score: ScoreDetail
    attempts: int = Field(ge=1)
