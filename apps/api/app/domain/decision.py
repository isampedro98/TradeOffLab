from datetime import datetime
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
    question: str
    context: str
    type: DecisionType
    status: DecisionStatus
    created_at: datetime

