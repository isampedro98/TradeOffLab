from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.domain.assumption import AssumptionConfidence


class AssumptionRecord(Base):
    __tablename__ = "assumptions"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    decision_id: Mapped[str] = mapped_column(
        ForeignKey("decisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[AssumptionConfidence] = mapped_column(
        Enum(AssumptionConfidence, native_enum=False),
        nullable=False,
    )
    impact_if_false: Mapped[str] = mapped_column(Text, nullable=False)
    validation_method: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
