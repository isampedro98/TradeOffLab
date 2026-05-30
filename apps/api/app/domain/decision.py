from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DecisionStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    RECOMMENDED = "recommended"
    ARCHIVED = "archived"


class DecisionType(StrEnum):
    ERP_ADOPTION = "erp_adoption"
    ARCHITECTURE = "architecture"
    CLOUD_PROVIDER = "cloud_provider"
    BUILD_VS_BUY = "build_vs_buy"
    PROCUREMENT_AUTOMATION = "procurement_automation"
    SOFTWARE_STACK = "software_stack"
    STRATEGIC_TECHNICAL = "strategic_technical"


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable identifier for the decision.")
    title: str
    decision_brief: str
    question: str
    context: str
    type: DecisionType
    status: DecisionStatus
    created_at: datetime
    updated_at: datetime


class DecisionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    decision_brief: str
    question: str
    context: str
    type: DecisionType
    status: DecisionStatus = DecisionStatus.DRAFT


class DecisionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    decision_brief: str | None = None
    question: str | None = None
    context: str | None = None
    type: DecisionType | None = None
    status: DecisionStatus | None = None


def build_bootstrap_decision() -> Decision:
    return Decision(
        id="decision-database-bootstrap",
        title="PostgreSQL vs MySQL vs SQL Server",
        decision_brief="Evaluate three database platforms for the next transactional product stack.",
        question="Which primary OLTP database should we standardize on for the next product phase?",
        context=(
            "Bootstrap example for the TradeOffLab MVP. "
            "The team is choosing a default relational database for a new multi-service product. "
            "The decision must balance operational complexity, ecosystem fit, licensing exposure, "
            "and long-term maintainability."
        ),
        type=DecisionType.SOFTWARE_STACK,
        status=DecisionStatus.DRAFT,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
