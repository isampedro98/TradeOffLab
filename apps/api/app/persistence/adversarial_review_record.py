from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.domain.adversarial_review import AdversarialReviewSeverity


class AdversarialReviewRecord(Base):
    __tablename__ = "adversarial_reviews"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    decision_id: Mapped[str] = mapped_column(
        ForeignKey("decisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    overall_risk: Mapped[AdversarialReviewSeverity] = mapped_column(
        Enum(AdversarialReviewSeverity, native_enum=False),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AdversarialReviewFindingRecord(Base):
    __tablename__ = "adversarial_review_findings"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    review_id: Mapped[str] = mapped_column(
        ForeignKey("adversarial_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[AdversarialReviewSeverity] = mapped_column(
        Enum(AdversarialReviewSeverity, native_enum=False),
        nullable=False,
    )
    critique: Mapped[str] = mapped_column(Text, nullable=False)
    consequence: Mapped[str] = mapped_column(Text, nullable=False)
    mitigation_test: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
