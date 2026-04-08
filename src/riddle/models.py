from pydantic import BaseModel, Field


class ScoreDetail(BaseModel):
    uniqueness: bool
    structural_soundness: bool
    concrete_grounding: bool
    strict_score: float = Field(ge=0.0, le=10.0)
    passed: bool
    reason: str | None = None
    strict_review: str | None = None

    def expected_pass(self, strict_threshold: float) -> bool:
        return (
            self.structural_soundness
            and self.concrete_grounding
            and self.strict_score >= strict_threshold
        )


class RiddleResult(BaseModel):
    question: str
    answer: str
    pattern: str
    score: ScoreDetail
    attempts: int = Field(ge=1)
