from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.evidence import Evidence, EvidenceCreate, EvidenceUpdate
from app.persistence.decision_record import DecisionRecord
from app.persistence.evidence_record import EvidenceRecord


class EvidenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_decision(self, decision_id: str) -> list[Evidence]:
        statement = (
            select(EvidenceRecord)
            .where(EvidenceRecord.decision_id == decision_id)
            .order_by(EvidenceRecord.created_at.asc())
        )
        records = self.session.execute(statement).scalars().all()
        return [self._to_domain(record) for record in records]

    def get_for_decision(self, decision_id: str, evidence_id: str) -> Evidence | None:
        statement = select(EvidenceRecord).where(
            EvidenceRecord.decision_id == decision_id,
            EvidenceRecord.id == evidence_id,
        )
        record = self.session.execute(statement).scalar_one_or_none()
        if record is None:
            return None
        return self._to_domain(record)

    def create(self, decision_id: str, payload: EvidenceCreate) -> Evidence:
        now = datetime.now(UTC)
        record = EvidenceRecord(
            id=f"evidence-{uuid4().hex}",
            decision_id=decision_id,
            title=payload.title,
            summary=payload.summary,
            source=payload.source,
            created_at=now,
            updated_at=now,
        )
        self.session.add(record)
        self._touch_decision(decision_id, timestamp=now)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def update(self, decision_id: str, evidence_id: str, payload: EvidenceUpdate) -> Evidence | None:
        statement = select(EvidenceRecord).where(
            EvidenceRecord.decision_id == decision_id,
            EvidenceRecord.id == evidence_id,
        )
        record = self.session.execute(statement).scalar_one_or_none()
        if record is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(record, field_name, value)
        record.updated_at = datetime.now(UTC)
        self._touch_decision(decision_id, timestamp=record.updated_at)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def delete(self, decision_id: str, evidence_id: str) -> bool:
        statement = select(EvidenceRecord).where(
            EvidenceRecord.decision_id == decision_id,
            EvidenceRecord.id == evidence_id,
        )
        record = self.session.execute(statement).scalar_one_or_none()
        if record is None:
            return False

        now = datetime.now(UTC)
        self.session.delete(record)
        self._touch_decision(decision_id, timestamp=now)
        self.session.commit()
        return True

    def create_if_missing(self, evidence: Evidence) -> Evidence:
        existing = self.session.get(EvidenceRecord, evidence.id)
        if existing is not None:
            return self._to_domain(existing)

        record = EvidenceRecord(
            id=evidence.id,
            decision_id=evidence.decision_id,
            title=evidence.title,
            summary=evidence.summary,
            source=evidence.source,
            created_at=evidence.created_at,
            updated_at=evidence.updated_at,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def _touch_decision(self, decision_id: str, *, timestamp: datetime) -> None:
        decision = self.session.get(DecisionRecord, decision_id)
        if decision is not None:
            decision.updated_at = timestamp

    @staticmethod
    def _to_domain(record: EvidenceRecord) -> Evidence:
        return Evidence(
            id=record.id,
            decision_id=record.decision_id,
            title=record.title,
            summary=record.summary,
            source=record.source,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
