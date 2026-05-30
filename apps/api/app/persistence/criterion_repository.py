from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.criterion import Criterion, CriterionCreate, CriterionUpdate
from app.persistence.criterion_record import CriterionRecord
from app.persistence.decision_record import DecisionRecord


class CriterionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_decision(self, decision_id: str) -> list[Criterion]:
        statement = (
            select(CriterionRecord)
            .where(CriterionRecord.decision_id == decision_id)
            .order_by(CriterionRecord.created_at.asc())
        )
        records = self.session.execute(statement).scalars().all()
        return [self._to_domain(record) for record in records]

    def get_for_decision(self, decision_id: str, criterion_id: str) -> Criterion | None:
        statement = select(CriterionRecord).where(
            CriterionRecord.decision_id == decision_id,
            CriterionRecord.id == criterion_id,
        )
        record = self.session.execute(statement).scalar_one_or_none()
        if record is None:
            return None
        return self._to_domain(record)

    def create(self, decision_id: str, payload: CriterionCreate) -> Criterion:
        now = datetime.now(UTC)
        record = CriterionRecord(
            id=f"criterion-{uuid4().hex}",
            decision_id=decision_id,
            name=payload.name,
            description=payload.description,
            weight=payload.weight,
            measurement_type=payload.measurement_type,
            created_at=now,
            updated_at=now,
        )
        self.session.add(record)
        self._touch_decision(decision_id, timestamp=now)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def update(
        self,
        decision_id: str,
        criterion_id: str,
        payload: CriterionUpdate,
    ) -> Criterion | None:
        statement = select(CriterionRecord).where(
            CriterionRecord.decision_id == decision_id,
            CriterionRecord.id == criterion_id,
        )
        record = self.session.execute(statement).scalar_one_or_none()
        if record is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(record, field_name, value)

        now = datetime.now(UTC)
        record.updated_at = now
        self._touch_decision(decision_id, timestamp=now)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def delete(self, decision_id: str, criterion_id: str) -> bool:
        statement = select(CriterionRecord).where(
            CriterionRecord.decision_id == decision_id,
            CriterionRecord.id == criterion_id,
        )
        record = self.session.execute(statement).scalar_one_or_none()
        if record is None:
            return False

        now = datetime.now(UTC)
        self.session.delete(record)
        self._touch_decision(decision_id, timestamp=now)
        self.session.commit()
        return True

    def create_if_missing(self, criterion: Criterion) -> Criterion:
        existing = self.session.get(CriterionRecord, criterion.id)
        if existing is not None:
            return self._to_domain(existing)

        record = CriterionRecord(
            id=criterion.id,
            decision_id=criterion.decision_id,
            name=criterion.name,
            description=criterion.description,
            weight=criterion.weight,
            measurement_type=criterion.measurement_type,
            created_at=criterion.created_at,
            updated_at=criterion.updated_at,
        )
        self.session.add(record)
        self._touch_decision(criterion.decision_id, timestamp=criterion.updated_at)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def _touch_decision(self, decision_id: str, *, timestamp: datetime) -> None:
        decision = self.session.get(DecisionRecord, decision_id)
        if decision is not None:
            decision.updated_at = timestamp

    @staticmethod
    def _to_domain(record: CriterionRecord) -> Criterion:
        return Criterion(
            id=record.id,
            decision_id=record.decision_id,
            name=record.name,
            description=record.description,
            weight=record.weight,
            measurement_type=record.measurement_type,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
