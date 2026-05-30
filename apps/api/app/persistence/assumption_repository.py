from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.assumption import Assumption, AssumptionCreate, AssumptionUpdate
from app.persistence.assumption_record import AssumptionRecord
from app.persistence.decision_record import DecisionRecord


class AssumptionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_decision(self, decision_id: str) -> list[Assumption]:
        statement = (
            select(AssumptionRecord)
            .where(AssumptionRecord.decision_id == decision_id)
            .order_by(AssumptionRecord.created_at.asc())
        )
        records = self.session.execute(statement).scalars().all()
        return [self._to_domain(record) for record in records]

    def get_for_decision(self, decision_id: str, assumption_id: str) -> Assumption | None:
        statement = select(AssumptionRecord).where(
            AssumptionRecord.decision_id == decision_id,
            AssumptionRecord.id == assumption_id,
        )
        record = self.session.execute(statement).scalar_one_or_none()
        if record is None:
            return None
        return self._to_domain(record)

    def create(self, decision_id: str, payload: AssumptionCreate) -> Assumption:
        now = datetime.now(UTC)
        record = AssumptionRecord(
            id=f"assumption-{uuid4().hex}",
            decision_id=decision_id,
            statement=payload.statement,
            confidence=payload.confidence,
            impact_if_false=payload.impact_if_false,
            validation_method=payload.validation_method,
            created_at=now,
            updated_at=now,
        )
        self.session.add(record)
        self._touch_decision(decision_id, timestamp=now)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def create_many(
        self,
        decision_id: str,
        payloads: list[AssumptionCreate],
    ) -> list[Assumption]:
        now = datetime.now(UTC)
        records = [
            AssumptionRecord(
                id=f"assumption-{uuid4().hex}",
                decision_id=decision_id,
                statement=payload.statement,
                confidence=payload.confidence,
                impact_if_false=payload.impact_if_false,
                validation_method=payload.validation_method,
                created_at=now,
                updated_at=now,
            )
            for payload in payloads
        ]
        self.session.add_all(records)
        self._touch_decision(decision_id, timestamp=now)
        self.session.commit()
        return [self._to_domain(record) for record in records]

    def update(
        self,
        decision_id: str,
        assumption_id: str,
        payload: AssumptionUpdate,
    ) -> Assumption | None:
        statement = select(AssumptionRecord).where(
            AssumptionRecord.decision_id == decision_id,
            AssumptionRecord.id == assumption_id,
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

    def delete(self, decision_id: str, assumption_id: str) -> bool:
        statement = select(AssumptionRecord).where(
            AssumptionRecord.decision_id == decision_id,
            AssumptionRecord.id == assumption_id,
        )
        record = self.session.execute(statement).scalar_one_or_none()
        if record is None:
            return False

        now = datetime.now(UTC)
        self.session.delete(record)
        self._touch_decision(decision_id, timestamp=now)
        self.session.commit()
        return True

    def create_if_missing(self, assumption: Assumption) -> Assumption:
        existing = self.session.get(AssumptionRecord, assumption.id)
        if existing is not None:
            return self._to_domain(existing)

        record = AssumptionRecord(
            id=assumption.id,
            decision_id=assumption.decision_id,
            statement=assumption.statement,
            confidence=assumption.confidence,
            impact_if_false=assumption.impact_if_false,
            validation_method=assumption.validation_method,
            created_at=assumption.created_at,
            updated_at=assumption.updated_at,
        )
        self.session.add(record)
        self._touch_decision(assumption.decision_id, timestamp=assumption.updated_at)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def replace_for_decision(
        self,
        decision_id: str,
        payloads: list[AssumptionCreate],
    ) -> list[Assumption]:
        now = datetime.now(UTC)
        existing_records = self.session.execute(
            select(AssumptionRecord).where(AssumptionRecord.decision_id == decision_id)
        ).scalars().all()
        for record in existing_records:
            self.session.delete(record)

        records = [
            AssumptionRecord(
                id=f"assumption-{uuid4().hex}",
                decision_id=decision_id,
                statement=payload.statement,
                confidence=payload.confidence,
                impact_if_false=payload.impact_if_false,
                validation_method=payload.validation_method,
                created_at=now,
                updated_at=now,
            )
            for payload in payloads
        ]
        self.session.add_all(records)
        self._touch_decision(decision_id, timestamp=now)
        self.session.commit()
        return [self._to_domain(record) for record in records]

    def _touch_decision(self, decision_id: str, *, timestamp: datetime) -> None:
        decision = self.session.get(DecisionRecord, decision_id)
        if decision is not None:
            decision.updated_at = timestamp

    @staticmethod
    def _to_domain(record: AssumptionRecord) -> Assumption:
        return Assumption(
            id=record.id,
            decision_id=record.decision_id,
            statement=record.statement,
            confidence=record.confidence,
            impact_if_false=record.impact_if_false,
            validation_method=record.validation_method,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
