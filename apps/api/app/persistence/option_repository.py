from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.option import Option, OptionCreate, OptionUpdate
from app.persistence.decision_record import DecisionRecord
from app.persistence.option_record import OptionRecord


class OptionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_decision(self, decision_id: str) -> list[Option]:
        statement = (
            select(OptionRecord)
            .where(OptionRecord.decision_id == decision_id)
            .order_by(OptionRecord.created_at.asc())
        )
        records = self.session.execute(statement).scalars().all()
        return [self._to_domain(record) for record in records]

    def get_for_decision(self, decision_id: str, option_id: str) -> Option | None:
        statement = select(OptionRecord).where(
            OptionRecord.decision_id == decision_id,
            OptionRecord.id == option_id,
        )
        record = self.session.execute(statement).scalar_one_or_none()
        if record is None:
            return None
        return self._to_domain(record)

    def create(self, decision_id: str, payload: OptionCreate) -> Option:
        now = datetime.now(UTC)
        record = OptionRecord(
            id=f"option-{uuid4().hex}",
            decision_id=decision_id,
            name=payload.name,
            description=payload.description,
            created_at=now,
            updated_at=now,
        )
        self.session.add(record)
        self._touch_decision(decision_id, timestamp=now)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def update(self, decision_id: str, option_id: str, payload: OptionUpdate) -> Option | None:
        statement = select(OptionRecord).where(
            OptionRecord.decision_id == decision_id,
            OptionRecord.id == option_id,
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

    def delete(self, decision_id: str, option_id: str) -> bool:
        statement = select(OptionRecord).where(
            OptionRecord.decision_id == decision_id,
            OptionRecord.id == option_id,
        )
        record = self.session.execute(statement).scalar_one_or_none()
        if record is None:
            return False

        now = datetime.now(UTC)
        self.session.delete(record)
        self._touch_decision(decision_id, timestamp=now)
        self.session.commit()
        return True

    def create_if_missing(self, option: Option) -> Option:
        existing = self.session.get(OptionRecord, option.id)
        if existing is not None:
            return self._to_domain(existing)

        record = OptionRecord(
            id=option.id,
            decision_id=option.decision_id,
            name=option.name,
            description=option.description,
            created_at=option.created_at,
            updated_at=option.updated_at,
        )
        self.session.add(record)
        self._touch_decision(option.decision_id, timestamp=option.updated_at)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def _touch_decision(self, decision_id: str, *, timestamp: datetime) -> None:
        decision = self.session.get(DecisionRecord, decision_id)
        if decision is not None:
            decision.updated_at = timestamp

    @staticmethod
    def _to_domain(record: OptionRecord) -> Option:
        return Option(
            id=record.id,
            decision_id=record.decision_id,
            name=record.name,
            description=record.description,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
