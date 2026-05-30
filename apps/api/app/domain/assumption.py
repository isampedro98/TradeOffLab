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
            id=f"{decision_id}-assumption-relational-workload",
            decision_id=decision_id,
            statement=(
                "The core workload for the next product phase will remain relational and transaction-heavy."
            ),
            confidence=AssumptionConfidence.MEDIUM,
            impact_if_false=(
                "A non-relational or analytics-heavy workload would weaken the relevance of this database comparison."
            ),
            validation_method=(
                "Review current service boundaries, query patterns, and expected growth in transactional volume."
            ),
            created_at=now,
            updated_at=now,
        ),
        Assumption(
            id=f"{decision_id}-assumption-license-sensitivity",
            decision_id=decision_id,
            statement=(
                "Licensing cost and vendor lock-in are material concerns for the platform team."
            ),
            confidence=AssumptionConfidence.MEDIUM,
            impact_if_false=(
                "A commercial platform may be undervalued if budget sensitivity is lower than assumed."
            ),
            validation_method=(
                "Validate budget constraints and procurement posture with engineering leadership and finance."
            ),
            created_at=now,
            updated_at=now,
        ),
        Assumption(
            id=f"{decision_id}-assumption-managed-hosting",
            decision_id=decision_id,
            statement=(
                "The team can rely on managed hosting or strong automation for backups, failover, and monitoring."
            ),
            confidence=AssumptionConfidence.MEDIUM,
            impact_if_false=(
                "Operational burden would become a heavier decision factor than currently reflected."
            ),
            validation_method=(
                "Confirm infrastructure strategy, SRE capacity, and hosting constraints before final selection."
            ),
            created_at=now,
            updated_at=now,
        ),
    ]
