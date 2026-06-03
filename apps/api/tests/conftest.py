import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.db import Base
from app.domain.assumption import build_bootstrap_assumptions
from app.domain.criterion import build_bootstrap_criteria
from app.domain.decision import build_bootstrap_decision
from app.domain.option import build_bootstrap_options
from app.persistence.adversarial_review_record import (
    AdversarialReviewFindingRecord,
    AdversarialReviewRecord,
)
from app.persistence.assumption_record import AssumptionRecord
from app.persistence.criterion_record import CriterionRecord
from app.persistence.decision_record import DecisionRecord
from app.persistence.evidence_record import EvidenceRecord
from app.persistence.option_record import OptionRecord
from app.persistence.recommendation_memo_record import (
    RecommendationConditionRecord,
    RecommendationMemoRecord,
)
from app.persistence.tradeoff_matrix_record import (
    TradeoffAssessmentRecord,
    TradeoffMatrixRecord,
)
from app.persistence.assumption_repository import AssumptionRepository
from app.persistence.criterion_repository import CriterionRepository
from app.persistence.decision_repository import DecisionRepository
from app.persistence.option_repository import OptionRepository


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def decision_id() -> str:
    return "decision-database-bootstrap"


@pytest.fixture
def seeded_decision(db_session: Session, decision_id: str):
    decision_repository = DecisionRepository(db_session)
    option_repository = OptionRepository(db_session)
    criterion_repository = CriterionRepository(db_session)
    assumption_repository = AssumptionRepository(db_session)

    decision = build_bootstrap_decision()
    decision_repository.create_if_missing(decision)
    for option in build_bootstrap_options(decision_id):
        option_repository.create_if_missing(option)
    for criterion in build_bootstrap_criteria(decision_id):
        criterion_repository.create_if_missing(criterion)
    for assumption in build_bootstrap_assumptions(decision_id):
        assumption_repository.create_if_missing(assumption)

    return decision_id


@pytest.fixture
def minimal_assumption_payload():
    from app.domain.assumption import AssumptionConfidence, AssumptionCreate
    from app.services.assumption_generation import GeneratedAssumptionsPayload

    return GeneratedAssumptionsPayload(
        assumptions=[
            AssumptionCreate(
                statement="Team capacity stays flat through the evaluation window.",
                confidence=AssumptionConfidence.MEDIUM,
                impact_if_false="Timeline pressure would invalidate vendor comparison results.",
                validation_method="Confirm hiring plan with engineering leadership.",
            )
        ]
    )


@pytest.fixture
def minimal_criteria_payload():
    from app.domain.criterion import CriterionCreate, CriterionMeasurementType
    from app.services.criteria_generation import GeneratedCriteriaPayload

    return GeneratedCriteriaPayload(
        criteria=[
            CriterionCreate(
                name="Operational complexity",
                description="Measure migration, observability, reliability, and day-two operational burden.",
                weight=0.55,
                measurement_type=CriterionMeasurementType.QUALITATIVE,
            ),
            CriterionCreate(
                name="Economic efficiency",
                description="Measure cost exposure across infrastructure, licensing, and support.",
                weight=0.45,
                measurement_type=CriterionMeasurementType.NUMERIC,
            ),
        ]
    )


@pytest.fixture
def minimal_evidence_payload():
    from datetime import UTC, datetime

    from app.domain.evidence import EvidenceCreate, EvidenceSourceType
    from app.services.evidence_generation import GeneratedEvidencePayload, ReviewedEvidencePayload

    now = datetime.now(UTC)

    generated = GeneratedEvidencePayload(
        evidence=[
            EvidenceCreate(
                title="Managed service SLA comparison",
                summary="Compare uptime commitments, backup posture, and maintenance windows across shortlisted providers.",
                source="Vendor SLA documentation",
                source_type=EvidenceSourceType.WEB_CAPTURE,
                source_url="https://example.com/vendor-sla",
                source_query="managed service database SLA comparison",
                excerpt="The provider documents uptime commitments, maintenance windows, and backup posture.",
                retrieved_at=now,
                retrieval_agent="researcher",
            ),
            EvidenceCreate(
                title="Three-year TCO baseline",
                summary="Estimate infrastructure, licensing, staffing, and migration costs across the candidate options.",
                source="Cloud pricing and licensing analysis",
                source_type=EvidenceSourceType.WEB_CAPTURE,
                source_url="https://example.com/tco-analysis",
                source_query="database total cost ownership licensing managed service",
                excerpt="The article compares infrastructure, licensing, and staffing costs over three years.",
                retrieved_at=now,
                retrieval_agent="researcher",
            ),
        ]
    )
    reviewed = ReviewedEvidencePayload(evidence=generated.evidence)
    return {
        "generated": generated,
        "reviewed": reviewed,
    }
