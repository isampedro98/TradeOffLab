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
        id="decision-erp-bootstrap",
        title="ERPNext vs Tango vs Bejerman",
        decision_brief="Evaluate three ERP options for local adoption and implementation risk.",
        question="Should we adopt ERPNext instead of Tango or Bejerman?",
        context=(
            "Bootstrap example for the TradeOffLab MVP. "
            "The goal is to model a local-first, structured decision workflow."
        ),
        type=DecisionType.ERP_ADOPTION,
        status=DecisionStatus.DRAFT,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
