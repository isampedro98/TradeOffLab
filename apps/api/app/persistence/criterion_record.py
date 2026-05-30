from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.domain.criterion import CriterionMeasurementType


class CriterionRecord(Base):
    __tablename__ = "criteria"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    decision_id: Mapped[str] = mapped_column(
        ForeignKey("decisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    measurement_type: Mapped[CriterionMeasurementType] = mapped_column(
        Enum(CriterionMeasurementType, native_enum=False),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
