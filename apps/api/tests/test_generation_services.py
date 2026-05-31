import pytest
from sqlalchemy.orm import Session

from app.domain.adversarial_review import (
    AdversarialReviewFindingCreate,
    AdversarialReviewSeverity,
)
from app.domain.assumption import AssumptionConfidence
from app.domain.criterion import build_bootstrap_criteria
from app.domain.decision import build_bootstrap_decision
from app.domain.option import build_bootstrap_options
from app.domain.recommendation_memo import (
    RecommendationConditionCreate,
    RecommendationConfidence,
)
from app.domain.tradeoff_matrix import TradeoffAssessmentCreate
from app.persistence.decision_repository import DecisionRepository
from app.services.adversarial_review_generation import (
    AdversarialReviewGenerationRequest,
    AdversarialReviewGenerationService,
    GeneratedAdversarialReviewPayload,
)
from app.services.assumption_generation import (
    AssumptionGenerationRequest,
    AssumptionGenerationService,
    GeneratedAssumptionsPayload,
)
from app.services.recommendation_memo_generation import (
    GeneratedRecommendationMemoPayload,
    RecommendationMemoGenerationRequest,
    RecommendationMemoGenerationService,
)
from app.services.tradeoff_matrix_generation import (
    GeneratedTradeoffMatrixPayload,
    TradeoffMatrixGenerationRequest,
    TradeoffMatrixGenerationService,
)
from tests.stub_litellm_client import StubLiteLLMClient


def _build_tradeoff_payload(decision_id: str) -> GeneratedTradeoffMatrixPayload:
    options = build_bootstrap_options(decision_id)
    criteria = build_bootstrap_criteria(decision_id)
    assessments = [
        TradeoffAssessmentCreate(
            criterion_id=criterion.id,
            option_id=option.id,
            score=3.0,
            rationale=f"Assessment for {criterion.name} vs {option.name}.",
        )
        for criterion in criteria
        for option in options
    ]
    return GeneratedTradeoffMatrixPayload(
        summary="PostgreSQL leads on ecosystem fit with acceptable operational cost.",
        scoring_scale_label="1 = weak fit, 5 = strong fit",
        assessments=assessments,
    )


def test_assumption_generation_requires_options(db_session: Session, decision_id: str) -> None:
    DecisionRepository(db_session).create_if_missing(build_bootstrap_decision())
    service = AssumptionGenerationService(
        db_session,
        client=StubLiteLLMClient(responses={}),
    )

    with pytest.raises(ValueError, match="at least one option"):
        service.generate_for_decision(
            decision_id,
            AssumptionGenerationRequest(count=1),
        )


def test_assumption_generation_persists_stubbed_response(
    db_session: Session,
    seeded_decision: str,
    minimal_assumption_payload: GeneratedAssumptionsPayload,
) -> None:
    stub = StubLiteLLMClient(
        responses={GeneratedAssumptionsPayload: minimal_assumption_payload},
        model="stub-assumptions",
    )
    service = AssumptionGenerationService(db_session, client=stub)

    response = service.generate_for_decision(
        seeded_decision,
        AssumptionGenerationRequest(count=1, replace_existing=True),
    )

    assert response.model == "stub-assumptions"
    assert len(response.assumptions) == 1
    assert response.assumptions[0].statement.startswith("Team capacity")
    assert len(stub.calls) == 1
    user_content = stub.calls[0]["messages"][1]["content"]
    assert "Generate exactly 1 assumptions" in user_content
    assert seeded_decision in user_content


def test_tradeoff_matrix_generation_validates_full_grid(
    db_session: Session,
    seeded_decision: str,
) -> None:
    payload = _build_tradeoff_payload(seeded_decision)
    assessments = payload.assessments
    assessments.pop()
    incomplete = GeneratedTradeoffMatrixPayload(
        summary=payload.summary,
        scoring_scale_label=payload.scoring_scale_label,
        assessments=assessments,
    )
    stub = StubLiteLLMClient(responses={GeneratedTradeoffMatrixPayload: incomplete})
    service = TradeoffMatrixGenerationService(db_session, client=stub)

    with pytest.raises(ValueError, match="every criterion-option pair"):
        service.generate_for_decision(
            seeded_decision,
            TradeoffMatrixGenerationRequest(),
        )


def test_tradeoff_matrix_generation_persists_stubbed_response(
    db_session: Session,
    seeded_decision: str,
) -> None:
    payload = _build_tradeoff_payload(seeded_decision)
    stub = StubLiteLLMClient(
        responses={GeneratedTradeoffMatrixPayload: payload},
        model="stub-tradeoffs",
    )
    service = TradeoffMatrixGenerationService(db_session, client=stub)

    response = service.generate_for_decision(
        seeded_decision,
        TradeoffMatrixGenerationRequest(),
    )

    assert response.matrix.model == "stub-tradeoffs"
    assert len(response.matrix.assessments) == 12
    assert "PostgreSQL leads" in response.matrix.summary
    assert stub.calls[0]["response_model"] is GeneratedTradeoffMatrixPayload


def test_adversarial_review_generation_requires_tradeoff_matrix(
    db_session: Session,
    seeded_decision: str,
) -> None:
    service = AdversarialReviewGenerationService(
        db_session,
        client=StubLiteLLMClient(responses={}),
    )

    with pytest.raises(ValueError, match="tradeoff matrix"):
        service.generate_for_decision(
            seeded_decision,
            AdversarialReviewGenerationRequest(),
        )


def test_adversarial_review_generation_persists_stubbed_response(
    db_session: Session,
    seeded_decision: str,
) -> None:
    tradeoff_service = TradeoffMatrixGenerationService(
        db_session,
        client=StubLiteLLMClient(
            responses={GeneratedTradeoffMatrixPayload: _build_tradeoff_payload(seeded_decision)},
        ),
    )
    tradeoff_service.generate_for_decision(
        seeded_decision,
        TradeoffMatrixGenerationRequest(),
    )

    review_payload = GeneratedAdversarialReviewPayload(
        summary="Licensing exposure remains under-explored.",
        overall_risk=AdversarialReviewSeverity.MEDIUM,
        findings=[
            AdversarialReviewFindingCreate(
                title="Commercial licensing blind spot",
                severity=AdversarialReviewSeverity.MEDIUM,
                critique="SQL Server cost scenarios are thin.",
                consequence="Budget overrun risk at scale.",
                mitigation_test="Model three-year TCO with realistic core counts.",
            )
        ],
    )
    stub = StubLiteLLMClient(
        responses={GeneratedAdversarialReviewPayload: review_payload},
        model="stub-adversarial",
    )
    service = AdversarialReviewGenerationService(db_session, client=stub)

    response = service.generate_for_decision(
        seeded_decision,
        AdversarialReviewGenerationRequest(),
    )

    assert response.review.model == "stub-adversarial"
    assert response.review.overall_risk == AdversarialReviewSeverity.MEDIUM
    assert len(response.review.findings) == 1


def test_recommendation_memo_generation_requires_prerequisites(
    db_session: Session,
    seeded_decision: str,
) -> None:
    service = RecommendationMemoGenerationService(
        db_session,
        client=StubLiteLLMClient(responses={}),
    )

    with pytest.raises(ValueError, match="tradeoff matrix"):
        service.generate_for_decision(
            seeded_decision,
            RecommendationMemoGenerationRequest(),
        )


def test_recommendation_memo_generation_persists_stubbed_response(
    db_session: Session,
    seeded_decision: str,
) -> None:
    tradeoff_service = TradeoffMatrixGenerationService(
        db_session,
        client=StubLiteLLMClient(
            responses={GeneratedTradeoffMatrixPayload: _build_tradeoff_payload(seeded_decision)},
        ),
    )
    tradeoff_service.generate_for_decision(
        seeded_decision,
        TradeoffMatrixGenerationRequest(),
    )

    review_payload = GeneratedAdversarialReviewPayload(
        summary="Risk is manageable with explicit TCO validation.",
        overall_risk=AdversarialReviewSeverity.LOW,
        findings=[
            AdversarialReviewFindingCreate(
                title="TCO still provisional",
                severity=AdversarialReviewSeverity.LOW,
                critique="Cost model depends on unvalidated core counts.",
                consequence="Recommendation confidence should stay conditional.",
                mitigation_test="Finalize infrastructure sizing assumptions.",
            )
        ],
    )
    AdversarialReviewGenerationService(
        db_session,
        client=StubLiteLLMClient(
            responses={GeneratedAdversarialReviewPayload: review_payload},
        ),
    ).generate_for_decision(seeded_decision, AdversarialReviewGenerationRequest())

    recommended_option_id = f"{seeded_decision}-option-postgresql"
    fallback_option_id = f"{seeded_decision}-option-mysql"
    memo_payload = GeneratedRecommendationMemoPayload(
        recommended_option_id=recommended_option_id,
        fallback_option_id=fallback_option_id,
        rationale="PostgreSQL best matches ecosystem and operational criteria.",
        confidence=RecommendationConfidence.MEDIUM,
        conditions=[
            RecommendationConditionCreate(
                statement="Team completes a three-year TCO comparison before final approval.",
            )
        ],
    )
    stub = StubLiteLLMClient(
        responses={GeneratedRecommendationMemoPayload: memo_payload},
        model="stub-recommendation",
    )
    service = RecommendationMemoGenerationService(db_session, client=stub)

    response = service.generate_for_decision(
        seeded_decision,
        RecommendationMemoGenerationRequest(),
    )

    assert response.memo.model == "stub-recommendation"
    assert response.memo.recommended_option_id == recommended_option_id
    assert response.memo.fallback_option_id == fallback_option_id
    assert len(response.memo.conditions) == 1
