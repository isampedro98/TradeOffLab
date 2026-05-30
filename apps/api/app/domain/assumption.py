from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AssumptionConfidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Assumption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable identifier for the assumption.")
    decision_id: str
    statement: str
    confidence: AssumptionConfidence
    impact_if_false: str
    validation_method: str
    created_at: datetime
    updated_at: datetime


class AssumptionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: str
    confidence: AssumptionConfidence
    impact_if_false: str
    validation_method: str


class AssumptionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: str | None = None
    confidence: AssumptionConfidence | None = None
    impact_if_false: str | None = None
    validation_method: str | None = None


def build_bootstrap_assumptions(decision_id: str) -> list[Assumption]:
    now = datetime.now(UTC)
    return [
        Assumption(
            id=f"{decision_id}-assumption-customization-capacity",
            decision_id=decision_id,
            statement=(
                "The organization can absorb the technical and operational effort required to customize ERPNext."
            ),
            confidence=AssumptionConfidence.MEDIUM,
            impact_if_false=(
                "ERPNext could become slower and more expensive to adopt than expected."
            ),
            validation_method=(
                "Review internal technical capacity, implementation partner availability, and past ERP rollout capability."
            ),
            created_at=now,
            updated_at=now,
        ),
        Assumption(
            id=f"{decision_id}-assumption-local-support-matters",
            decision_id=decision_id,
            statement=(
                "Strong local support and market familiarity are materially important for successful ERP adoption."
            ),
            confidence=AssumptionConfidence.HIGH,
            impact_if_false=(
                "Local incumbents may be overvalued relative to more flexible alternatives."
            ),
            validation_method=(
                "Interview stakeholders responsible for operations, support expectations, and implementation escalation paths."
            ),
            created_at=now,
            updated_at=now,
        ),
        Assumption(
            id=f"{decision_id}-assumption-cost-weighting",
            decision_id=decision_id,
            statement=(
                "Total cost of ownership should remain one of the highest-weighted criteria in the ERP decision."
            ),
            confidence=AssumptionConfidence.MEDIUM,
            impact_if_false=(
                "The current recommendation framing may overweight cost relative to strategic fit or execution risk."
            ),
            validation_method=(
                "Validate weighting with leadership and compare against business priorities for the next 24 months."
            ),
            created_at=now,
            updated_at=now,
        ),
    ]
