from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EvidenceSourceType(StrEnum):
    MANUAL = "manual"
    AI_LEAD = "ai_lead"
    WEB_CAPTURE = "web_capture"


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable identifier for the evidence record.")
    decision_id: str
    title: str
    summary: str
    source: str
    source_type: EvidenceSourceType = EvidenceSourceType.MANUAL
    source_url: str | None = None
    source_query: str | None = None
    excerpt: str | None = None
    retrieved_at: datetime | None = None
    retrieval_agent: str | None = None
    created_at: datetime
    updated_at: datetime


class EvidenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    summary: str
    source: str
    source_type: EvidenceSourceType = EvidenceSourceType.MANUAL
    source_url: str | None = None
    source_query: str | None = None
    excerpt: str | None = None
    retrieved_at: datetime | None = None
    retrieval_agent: str | None = None


class EvidenceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    summary: str | None = None
    source: str | None = None
    source_type: EvidenceSourceType | None = None
    source_url: str | None = None
    source_query: str | None = None
    excerpt: str | None = None
    retrieved_at: datetime | None = None
    retrieval_agent: str | None = None


def build_bootstrap_evidence(decision_id: str) -> list[Evidence]:
    now = datetime.now(UTC)
    return [
        Evidence(
            id=f"{decision_id}-evidence-postgresql-ecosystem",
            decision_id=decision_id,
            title="PostgreSQL extension and standards ecosystem",
            summary=(
                "The team values standards compliance, extensibility, and advanced SQL support. "
                "PostgreSQL is often favored when long-term flexibility and ecosystem breadth matter."
            ),
            source="Internal architecture notes and vendor landscape review",
            source_type=EvidenceSourceType.MANUAL,
            created_at=now,
            updated_at=now,
        ),
        Evidence(
            id=f"{decision_id}-evidence-managed-hosting",
            decision_id=decision_id,
            title="Managed hosting maturity across major clouds",
            summary=(
                "All shortlisted databases have strong managed offerings, but backup defaults, observability, "
                "HA posture, and operator familiarity still change operational fit."
            ),
            source="Platform evaluation workshop",
            source_type=EvidenceSourceType.MANUAL,
            created_at=now,
            updated_at=now,
        ),
        Evidence(
            id=f"{decision_id}-evidence-licensing",
            decision_id=decision_id,
            title="Licensing exposure and long-term TCO",
            summary=(
                "Licensing and enterprise feature packaging can materially affect long-term cost dynamics, "
                "especially for SQL Server and some MySQL enterprise paths."
            ),
            source="Finance and procurement review",
            source_type=EvidenceSourceType.MANUAL,
            created_at=now,
            updated_at=now,
        ),
    ]
