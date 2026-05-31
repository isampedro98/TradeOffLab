from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.recommendation_memo import (
    RecommendationCondition,
    RecommendationMemo,
    RecommendationMemoReplace,
)
from app.persistence.decision_record import DecisionRecord
from app.persistence.recommendation_memo_record import (
    RecommendationConditionRecord,
    RecommendationMemoRecord,
)


class RecommendationMemoRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_for_decision(self, decision_id: str) -> RecommendationMemo | None:
        statement = select(RecommendationMemoRecord).where(
            RecommendationMemoRecord.decision_id == decision_id
        )
        memo_record = self.session.execute(statement).scalar_one_or_none()
        if memo_record is None:
            return None
        return self._to_domain(memo_record)

    def replace_for_decision(
        self,
        decision_id: str,
        payload: RecommendationMemoReplace,
    ) -> RecommendationMemo:
        now = datetime.now(UTC)
        existing_memo = self.session.execute(
            select(RecommendationMemoRecord).where(
                RecommendationMemoRecord.decision_id == decision_id
            )
        ).scalar_one_or_none()

        if existing_memo is not None:
            existing_conditions = self.session.execute(
                select(RecommendationConditionRecord).where(
                    RecommendationConditionRecord.memo_id == existing_memo.id
                )
            ).scalars().all()
            for condition in existing_conditions:
                self.session.delete(condition)
            self.session.delete(existing_memo)
            self.session.flush()

        memo_id = f"recommendation-memo-{uuid4().hex}"
        memo_record = RecommendationMemoRecord(
            id=memo_id,
            decision_id=decision_id,
            recommended_option_id=payload.recommended_option_id,
            fallback_option_id=payload.fallback_option_id,
            rationale=payload.rationale,
            confidence=payload.confidence,
            provider=payload.provider,
            model=payload.model,
            created_at=now,
            updated_at=now,
        )
        self.session.add(memo_record)
        self.session.flush()

        condition_records = [
            RecommendationConditionRecord(
                id=f"recommendation-condition-{uuid4().hex}",
                memo_id=memo_id,
                position=index,
                statement=condition.statement,
                created_at=now,
                updated_at=now,
            )
            for index, condition in enumerate(payload.conditions)
        ]
        self.session.add_all(condition_records)
        self._touch_decision(decision_id, timestamp=now)
        self.session.commit()
        self.session.refresh(memo_record)
        return self._to_domain(memo_record)

    def _touch_decision(self, decision_id: str, *, timestamp: datetime) -> None:
        decision = self.session.get(DecisionRecord, decision_id)
        if decision is not None:
            decision.updated_at = timestamp

    def _to_domain(self, record: RecommendationMemoRecord) -> RecommendationMemo:
        condition_records = self.session.execute(
            select(RecommendationConditionRecord)
            .where(RecommendationConditionRecord.memo_id == record.id)
            .order_by(RecommendationConditionRecord.position.asc())
        ).scalars().all()
        conditions = [
            RecommendationCondition(
                id=condition_record.id,
                memo_id=condition_record.memo_id,
                position=condition_record.position,
                statement=condition_record.statement,
                created_at=condition_record.created_at,
                updated_at=condition_record.updated_at,
            )
            for condition_record in condition_records
        ]
        return RecommendationMemo(
            id=record.id,
            decision_id=record.decision_id,
            recommended_option_id=record.recommended_option_id,
            fallback_option_id=record.fallback_option_id,
            rationale=record.rationale,
            confidence=record.confidence,
            provider=record.provider,
            model=record.model,
            created_at=record.created_at,
            updated_at=record.updated_at,
            conditions=conditions,
        )
