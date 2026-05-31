from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.decision import Decision, DecisionCreate, DecisionUpdate
from app.persistence.decision_record import DecisionRecord


class DecisionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[Decision]:
        statement = select(DecisionRecord).order_by(DecisionRecord.created_at.desc())
        records = self.session.execute(statement).scalars().all()
        return [self._to_domain(record) for record in records]

    def get(self, decision_id: str) -> Decision | None:
        record = self.session.get(DecisionRecord, decision_id)
        if record is None:
            return None
        return self._to_domain(record)

    def create(self, payload: DecisionCreate, *, decision_id: str | None = None) -> Decision:
        now = datetime.now(UTC)
        record = DecisionRecord(
            id=decision_id or f"decision-{uuid4().hex}",
            title=payload.title,
            decision_brief=payload.decision_brief,
            question=payload.question,
            context=payload.context,
            type=payload.type,
            status=payload.status,
            created_at=now,
            updated_at=now,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def update(self, decision_id: str, payload: DecisionUpdate) -> Decision | None:
        record = self.session.get(DecisionRecord, decision_id)
        if record is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(record, field_name, value)
        record.updated_at = datetime.now(UTC)

        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def create_if_missing(self, decision: Decision) -> Decision:
        existing = self.session.get(DecisionRecord, decision.id)
        if existing is not None:
            return self._to_domain(existing)

        record = DecisionRecord(
            id=decision.id,
            title=decision.title,
            decision_brief=decision.decision_brief,
            question=decision.question,
            context=decision.context,
            type=decision.type,
            status=decision.status,
            created_at=decision.created_at,
            updated_at=decision.updated_at,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def delete(self, decision_id: str) -> bool:
        record = self.session.get(DecisionRecord, decision_id)
        if record is None:
            return False

        self.session.delete(record)
        self.session.commit()
        return True

    @staticmethod
    def _to_domain(record: DecisionRecord) -> Decision:
        return Decision(
            id=record.id,
            title=record.title,
            decision_brief=record.decision_brief,
            question=record.question,
            context=record.context,
            type=record.type,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
