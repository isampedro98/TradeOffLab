from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.tradeoff_matrix import (
    TradeoffAssessment,
    TradeoffMatrix,
    TradeoffMatrixReplace,
)
from app.persistence.decision_record import DecisionRecord
from app.persistence.tradeoff_matrix_record import (
    TradeoffAssessmentRecord,
    TradeoffMatrixRecord,
)


class TradeoffMatrixRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_for_decision(self, decision_id: str) -> TradeoffMatrix | None:
        statement = select(TradeoffMatrixRecord).where(
            TradeoffMatrixRecord.decision_id == decision_id
        )
        matrix_record = self.session.execute(statement).scalar_one_or_none()
        if matrix_record is None:
            return None
        return self._to_domain(matrix_record)

    def replace_for_decision(
        self,
        decision_id: str,
        payload: TradeoffMatrixReplace,
    ) -> TradeoffMatrix:
        now = datetime.now(UTC)
        existing_matrix = self.session.execute(
            select(TradeoffMatrixRecord).where(TradeoffMatrixRecord.decision_id == decision_id)
        ).scalar_one_or_none()

        if existing_matrix is not None:
            existing_assessments = self.session.execute(
                select(TradeoffAssessmentRecord).where(
                    TradeoffAssessmentRecord.matrix_id == existing_matrix.id
                )
            ).scalars().all()
            for assessment in existing_assessments:
                self.session.delete(assessment)
            self.session.delete(existing_matrix)
            self.session.flush()

        matrix_id = f"tradeoff-matrix-{uuid4().hex}"
        matrix_record = TradeoffMatrixRecord(
            id=matrix_id,
            decision_id=decision_id,
            summary=payload.summary,
            scoring_scale_label=payload.scoring_scale_label,
            provider=payload.provider,
            model=payload.model,
            created_at=now,
            updated_at=now,
        )
        self.session.add(matrix_record)
        self.session.flush()

        assessment_records = [
            TradeoffAssessmentRecord(
                id=f"tradeoff-assessment-{uuid4().hex}",
                matrix_id=matrix_id,
                criterion_id=assessment.criterion_id,
                option_id=assessment.option_id,
                score=assessment.score,
                rationale=assessment.rationale,
                created_at=now,
                updated_at=now,
            )
            for assessment in payload.assessments
        ]
        self.session.add_all(assessment_records)
        self._touch_decision(decision_id, timestamp=now)
        self.session.commit()
        self.session.refresh(matrix_record)
        return self._to_domain(matrix_record)

    def _touch_decision(self, decision_id: str, *, timestamp: datetime) -> None:
        decision = self.session.get(DecisionRecord, decision_id)
        if decision is not None:
            decision.updated_at = timestamp

    def _to_domain(self, record: TradeoffMatrixRecord) -> TradeoffMatrix:
        assessment_records = self.session.execute(
            select(TradeoffAssessmentRecord)
            .where(TradeoffAssessmentRecord.matrix_id == record.id)
            .order_by(
                TradeoffAssessmentRecord.criterion_id.asc(),
                TradeoffAssessmentRecord.option_id.asc(),
            )
        ).scalars().all()
        assessments = [
            TradeoffAssessment(
                id=assessment_record.id,
                matrix_id=assessment_record.matrix_id,
                criterion_id=assessment_record.criterion_id,
                option_id=assessment_record.option_id,
                score=assessment_record.score,
                rationale=assessment_record.rationale,
                created_at=assessment_record.created_at,
                updated_at=assessment_record.updated_at,
            )
            for assessment_record in assessment_records
        ]
        return TradeoffMatrix(
            id=record.id,
            decision_id=record.decision_id,
            summary=record.summary,
            scoring_scale_label=record.scoring_scale_label,
            provider=record.provider,
            model=record.model,
            created_at=record.created_at,
            updated_at=record.updated_at,
            assessments=assessments,
        )
