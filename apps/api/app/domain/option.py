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
            id=f"{decision_id}-option-postgresql",
            decision_id=decision_id,
            name="PostgreSQL",
            description=(
                "Open-source relational database with strong standards support, rich extensions, "
                "and broad adoption across modern application stacks."
            ),
            created_at=now,
            updated_at=now,
        ),
        Option(
            id=f"{decision_id}-option-mysql",
            decision_id=decision_id,
            name="MySQL",
            description=(
                "Widely deployed relational database with strong hosting availability, "
                "familiar operational patterns, and a mature ecosystem."
            ),
            created_at=now,
            updated_at=now,
        ),
        Option(
            id=f"{decision_id}-option-sqlserver",
            decision_id=decision_id,
            name="SQL Server",
            description=(
                "Commercial database platform with strong Microsoft integration, "
                "mature tooling, and enterprise support, but with licensing exposure."
            ),
            created_at=now,
            updated_at=now,
        ),
    ]
