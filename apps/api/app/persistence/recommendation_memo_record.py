from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.domain.recommendation_memo import RecommendationConfidence


class RecommendationMemoRecord(Base):
    __tablename__ = "recommendation_memos"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    decision_id: Mapped[str] = mapped_column(
        ForeignKey("decisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    recommended_option_id: Mapped[str] = mapped_column(
        ForeignKey("options.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fallback_option_id: Mapped[str | None] = mapped_column(
        ForeignKey("options.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[RecommendationConfidence] = mapped_column(
        Enum(RecommendationConfidence, native_enum=False),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RecommendationConditionRecord(Base):
    __tablename__ = "recommendation_conditions"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    memo_id: Mapped[str] = mapped_column(
        ForeignKey("recommendation_memos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
