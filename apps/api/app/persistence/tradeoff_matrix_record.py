from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TradeoffMatrixRecord(Base):
    __tablename__ = "tradeoff_matrices"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    decision_id: Mapped[str] = mapped_column(
        ForeignKey("decisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    scoring_scale_label: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TradeoffAssessmentRecord(Base):
    __tablename__ = "tradeoff_assessments"
    __table_args__ = (
        UniqueConstraint(
            "matrix_id",
            "criterion_id",
            "option_id",
            name="uq_tradeoff_assessments_matrix_criterion_option",
        ),
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    matrix_id: Mapped[str] = mapped_column(
        ForeignKey("tradeoff_matrices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    criterion_id: Mapped[str] = mapped_column(
        ForeignKey("criteria.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_id: Mapped[str] = mapped_column(
        ForeignKey("options.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score: Mapped[float] = mapped_column(nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
