from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TradeoffAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable identifier for the tradeoff assessment.")
    matrix_id: str
    criterion_id: str
    option_id: str
    score: float = Field(ge=1.0, le=5.0)
    rationale: str
    created_at: datetime
    updated_at: datetime


class TradeoffMatrix(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable identifier for the tradeoff matrix.")
    decision_id: str
    summary: str
    scoring_scale_label: str
    provider: str
    model: str
    created_at: datetime
    updated_at: datetime
    assessments: list[TradeoffAssessment]


class TradeoffAssessmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion_id: str
    option_id: str
    score: float = Field(ge=1.0, le=5.0)
    rationale: str


class TradeoffMatrixReplace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    scoring_scale_label: str
    provider: str
    model: str
    assessments: list[TradeoffAssessmentCreate] = Field(min_length=1)
