from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RecommendationConfidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecommendationCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable identifier for the recommendation condition.")
    memo_id: str
    position: int = Field(ge=0)
    statement: str
    created_at: datetime
    updated_at: datetime


class RecommendationMemo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable identifier for the recommendation memo.")
    decision_id: str
    recommended_option_id: str
    fallback_option_id: str | None = None
    rationale: str
    confidence: RecommendationConfidence
    provider: str
    model: str
    created_at: datetime
    updated_at: datetime
    conditions: list[RecommendationCondition]


class RecommendationConditionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: str


class RecommendationMemoReplace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommended_option_id: str
    fallback_option_id: str | None = None
    rationale: str
    confidence: RecommendationConfidence
    provider: str
    model: str
    conditions: list[RecommendationConditionCreate]
