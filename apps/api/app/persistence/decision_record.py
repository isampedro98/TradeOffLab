from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.domain.decision import DecisionStatus, DecisionType


class DecisionRecord(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    decision_brief: Mapped[str] = mapped_column(String(500), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[DecisionType] = mapped_column(
        Enum(DecisionType, native_enum=False),
        nullable=False,
    )
    status: Mapped[DecisionStatus] = mapped_column(
        Enum(DecisionStatus, native_enum=False),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
