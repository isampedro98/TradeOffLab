from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class Option(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable identifier for the option.")
    decision_id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime


class OptionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str


class OptionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None


def build_bootstrap_options(decision_id: str) -> list[Option]:
    now = datetime.now(UTC)
    return [
        Option(
            id=f"{decision_id}-option-erpnext",
            decision_id=decision_id,
            name="ERPNext",
            description=(
                "Open-source ERP with strong flexibility, broad customization options, "
                "and lower licensing cost, but more implementation ownership."
            ),
            created_at=now,
            updated_at=now,
        ),
        Option(
            id=f"{decision_id}-option-tango",
            decision_id=decision_id,
            name="Tango",
            description=(
                "Established ERP option with local market familiarity and vendor support, "
                "but potentially less flexibility and higher long-term licensing cost."
            ),
            created_at=now,
            updated_at=now,
        ),
        Option(
            id=f"{decision_id}-option-bejerman",
            decision_id=decision_id,
            name="Bejerman",
            description=(
                "Local ERP candidate with known administrative workflows and support channels, "
                "but with tradeoffs around adaptability and ecosystem breadth."
            ),
            created_at=now,
            updated_at=now,
        ),
    ]
