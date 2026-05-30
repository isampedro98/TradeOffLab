from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class CriterionMeasurementType(StrEnum):
    QUALITATIVE = "qualitative"
    NUMERIC = "numeric"
    BOOLEAN = "boolean"
    ORDINAL = "ordinal"


class Criterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable identifier for the criterion.")
    decision_id: str
    name: str
    description: str
    weight: float
    measurement_type: CriterionMeasurementType
    created_at: datetime
    updated_at: datetime


class CriterionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    weight: float
    measurement_type: CriterionMeasurementType


class CriterionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    weight: float | None = None
    measurement_type: CriterionMeasurementType | None = None


def build_bootstrap_criteria(decision_id: str) -> list[Criterion]:
    now = datetime.now(UTC)
    return [
        Criterion(
            id=f"{decision_id}-criterion-total-cost",
            decision_id=decision_id,
            name="Total Cost of Ownership",
            description=(
                "Evaluate licensing, implementation, customization, training, and support costs."
            ),
            weight=0.30,
            measurement_type=CriterionMeasurementType.NUMERIC,
            created_at=now,
            updated_at=now,
        ),
        Criterion(
            id=f"{decision_id}-criterion-functional-fit",
            decision_id=decision_id,
            name="Functional Fit",
            description=(
                "Measure how well each ERP matches the required business and administrative workflows."
            ),
            weight=0.30,
            measurement_type=CriterionMeasurementType.QUALITATIVE,
            created_at=now,
            updated_at=now,
        ),
        Criterion(
            id=f"{decision_id}-criterion-implementation-risk",
            decision_id=decision_id,
            name="Implementation Risk",
            description=(
                "Assess migration complexity, rollout risk, dependency on custom work, and project uncertainty."
            ),
            weight=0.25,
            measurement_type=CriterionMeasurementType.QUALITATIVE,
            created_at=now,
            updated_at=now,
        ),
        Criterion(
            id=f"{decision_id}-criterion-local-support",
            decision_id=decision_id,
            name="Local Support Availability",
            description=(
                "Evaluate availability of local implementation partners, support quality, and market familiarity."
            ),
            weight=0.15,
            measurement_type=CriterionMeasurementType.QUALITATIVE,
            created_at=now,
            updated_at=now,
        ),
    ]
