from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.adversarial_review import (
    AdversarialReview,
    AdversarialReviewFinding,
    AdversarialReviewReplace,
)
from app.persistence.adversarial_review_record import (
    AdversarialReviewFindingRecord,
    AdversarialReviewRecord,
)
from app.persistence.decision_record import DecisionRecord


class AdversarialReviewRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_for_decision(self, decision_id: str) -> AdversarialReview | None:
        statement = select(AdversarialReviewRecord).where(
            AdversarialReviewRecord.decision_id == decision_id
        )
        review_record = self.session.execute(statement).scalar_one_or_none()
        if review_record is None:
            return None
        return self._to_domain(review_record)

    def replace_for_decision(
        self,
        decision_id: str,
        payload: AdversarialReviewReplace,
    ) -> AdversarialReview:
        now = datetime.now(UTC)
        existing_review = self.session.execute(
            select(AdversarialReviewRecord).where(
                AdversarialReviewRecord.decision_id == decision_id
            )
        ).scalar_one_or_none()

        if existing_review is not None:
            existing_findings = self.session.execute(
                select(AdversarialReviewFindingRecord).where(
                    AdversarialReviewFindingRecord.review_id == existing_review.id
                )
            ).scalars().all()
            for finding in existing_findings:
                self.session.delete(finding)
            self.session.delete(existing_review)
            self.session.flush()

        review_id = f"adversarial-review-{uuid4().hex}"
        review_record = AdversarialReviewRecord(
            id=review_id,
            decision_id=decision_id,
            summary=payload.summary,
            overall_risk=payload.overall_risk,
            provider=payload.provider,
            model=payload.model,
            created_at=now,
            updated_at=now,
        )
        self.session.add(review_record)
        self.session.flush()

        finding_records = [
            AdversarialReviewFindingRecord(
                id=f"adversarial-review-finding-{uuid4().hex}",
                review_id=review_id,
                title=finding.title,
                severity=finding.severity,
                critique=finding.critique,
                consequence=finding.consequence,
                mitigation_test=finding.mitigation_test,
                created_at=now,
                updated_at=now,
            )
            for finding in payload.findings
        ]
        self.session.add_all(finding_records)
        self._touch_decision(decision_id, timestamp=now)
        self.session.commit()
        self.session.refresh(review_record)
        return self._to_domain(review_record)

    def _touch_decision(self, decision_id: str, *, timestamp: datetime) -> None:
        decision = self.session.get(DecisionRecord, decision_id)
        if decision is not None:
            decision.updated_at = timestamp

    def _to_domain(self, record: AdversarialReviewRecord) -> AdversarialReview:
        finding_records = self.session.execute(
            select(AdversarialReviewFindingRecord)
            .where(AdversarialReviewFindingRecord.review_id == record.id)
            .order_by(AdversarialReviewFindingRecord.created_at.asc())
        ).scalars().all()
        findings = [
            AdversarialReviewFinding(
                id=finding_record.id,
                review_id=finding_record.review_id,
                title=finding_record.title,
                severity=finding_record.severity,
                critique=finding_record.critique,
                consequence=finding_record.consequence,
                mitigation_test=finding_record.mitigation_test,
                created_at=finding_record.created_at,
                updated_at=finding_record.updated_at,
            )
            for finding_record in finding_records
        ]
        return AdversarialReview(
            id=record.id,
            decision_id=record.decision_id,
            summary=record.summary,
            overall_risk=record.overall_risk,
            provider=record.provider,
            model=record.model,
            created_at=record.created_at,
            updated_at=record.updated_at,
            findings=findings,
        )
