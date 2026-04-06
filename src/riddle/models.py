from pydantic import BaseModel, Field


class ScoreDetail(BaseModel):
    uniqueness: bool
    single_paradox: bool
    observation_based: bool

    @property
    def passed(self) -> bool:
        return self.uniqueness and self.single_paradox and self.observation_based


class RiddleResult(BaseModel):
    question: str
    answer: str
    pattern: str
    score: ScoreDetail
    attempts: int = Field(ge=1)
