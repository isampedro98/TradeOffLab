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
