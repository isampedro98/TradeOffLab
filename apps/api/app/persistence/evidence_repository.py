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
            source_type=payload.source_type,
            source_url=payload.source_url,
            source_query=payload.source_query,
            excerpt=payload.excerpt,
            retrieved_at=payload.retrieved_at,
            retrieval_agent=payload.retrieval_agent,
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
        payloads: list[EvidenceCreate],
    ) -> list[Evidence]:
        now = datetime.now(UTC)
        records = [
            EvidenceRecord(
                id=f"evidence-{uuid4().hex}",
                decision_id=decision_id,
                title=payload.title,
                summary=payload.summary,
                source=payload.source,
                source_type=payload.source_type,
                source_url=payload.source_url,
                source_query=payload.source_query,
                excerpt=payload.excerpt,
                retrieved_at=payload.retrieved_at,
                retrieval_agent=payload.retrieval_agent,
                created_at=now,
                updated_at=now,
            )
            for payload in payloads
        ]
        self.session.add_all(records)
        self._touch_decision(decision_id, timestamp=now)
        self.session.commit()
        return [self._to_domain(record) for record in records]

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
            source_type=evidence.source_type,
            source_url=evidence.source_url,
            source_query=evidence.source_query,
            excerpt=evidence.excerpt,
            retrieved_at=evidence.retrieved_at,
            retrieval_agent=evidence.retrieval_agent,
            created_at=evidence.created_at,
            updated_at=evidence.updated_at,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def replace_for_decision(
        self,
        decision_id: str,
        payloads: list[EvidenceCreate],
    ) -> list[Evidence]:
        now = datetime.now(UTC)
        existing_records = self.session.execute(
            select(EvidenceRecord).where(EvidenceRecord.decision_id == decision_id)
        ).scalars().all()
        for record in existing_records:
            self.session.delete(record)

        records = [
            EvidenceRecord(
                id=f"evidence-{uuid4().hex}",
                decision_id=decision_id,
                title=payload.title,
                summary=payload.summary,
                source=payload.source,
                source_type=payload.source_type,
                source_url=payload.source_url,
                source_query=payload.source_query,
                excerpt=payload.excerpt,
                retrieved_at=payload.retrieved_at,
                retrieval_agent=payload.retrieval_agent,
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
    def _to_domain(record: EvidenceRecord) -> Evidence:
        return Evidence(
            id=record.id,
            decision_id=record.decision_id,
            title=record.title,
            summary=record.summary,
            source=record.source,
            source_type=record.source_type,
            source_url=record.source_url,
            source_query=record.source_query,
            excerpt=record.excerpt,
            retrieved_at=record.retrieved_at,
            retrieval_agent=record.retrieval_agent,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
