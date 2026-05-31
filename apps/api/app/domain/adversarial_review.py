from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AdversarialReviewSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AdversarialReviewFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable identifier for the adversarial review finding.")
    review_id: str
    title: str
    severity: AdversarialReviewSeverity
    critique: str
    consequence: str
    mitigation_test: str
    created_at: datetime
    updated_at: datetime


class AdversarialReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable identifier for the adversarial review.")
    decision_id: str
    summary: str
    overall_risk: AdversarialReviewSeverity
    provider: str
    model: str
    created_at: datetime
    updated_at: datetime
    findings: list[AdversarialReviewFinding]


class AdversarialReviewFindingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    severity: AdversarialReviewSeverity
    critique: str
    consequence: str
    mitigation_test: str


class AdversarialReviewReplace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    overall_risk: AdversarialReviewSeverity
    provider: str
    model: str
    findings: list[AdversarialReviewFindingCreate] = Field(min_length=1)
