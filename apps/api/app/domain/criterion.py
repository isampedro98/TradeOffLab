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
            id=f"{decision_id}-criterion-operational-fit",
            decision_id=decision_id,
            name="Operational Fit",
            description=(
                "Evaluate backup strategy, replication, monitoring, migration tooling, and day-two operations."
            ),
            weight=0.30,
            measurement_type=CriterionMeasurementType.QUALITATIVE,
            created_at=now,
            updated_at=now,
        ),
        Criterion(
            id=f"{decision_id}-criterion-ecosystem-fit",
            decision_id=decision_id,
            name="Ecosystem Fit",
            description=(
                "Measure ORM support, hosting compatibility, extension availability, and integration fit with the current stack."
            ),
            weight=0.25,
            measurement_type=CriterionMeasurementType.QUALITATIVE,
            created_at=now,
            updated_at=now,
        ),
        Criterion(
            id=f"{decision_id}-criterion-total-cost",
            decision_id=decision_id,
            name="Total Cost of Ownership",
            description=(
                "Assess licensing, support, infrastructure, migration, and ongoing administration cost."
            ),
            weight=0.25,
            measurement_type=CriterionMeasurementType.NUMERIC,
            created_at=now,
            updated_at=now,
        ),
        Criterion(
            id=f"{decision_id}-criterion-team-familiarity",
            decision_id=decision_id,
            name="Team Familiarity",
            description=(
                "Evaluate how much internal knowledge already exists for administration, tuning, and troubleshooting."
            ),
            weight=0.20,
            measurement_type=CriterionMeasurementType.QUALITATIVE,
            created_at=now,
            updated_at=now,
        ),
    ]
