import pytest
from sqlalchemy.orm import Session

from app.domain.adversarial_review import (
    AdversarialReviewFindingCreate,
    AdversarialReviewSeverity,
)
from app.domain.assumption import AssumptionConfidence
from app.domain.criterion import build_bootstrap_criteria
from app.domain.decision import DecisionType, build_bootstrap_decision
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
from app.services.criteria_generation import (
    CriteriaGenerationRequest,
    CriteriaGenerationService,
    GeneratedCriteriaPayload,
)
from app.services.decision_context import CompactDecisionContext
from app.services.evidence_generation import (
    EvidenceResearchPlan,
    EvidenceGenerationRequest,
    EvidenceGenerationService,
    GeneratedEvidencePayload,
    PlannedResearchQuery,
    ReviewedEvidencePayload,
)
from app.services.recommendation_memo_generation import (
    GeneratedRecommendationMemoPayload,
    RecommendationMemoGenerationRequest,
    RecommendationMemoGenerationService,
)
from app.services.tradeoff_matrix_generation import (
    GeneratedTradeoffAssessmentPayload,
    TradeoffMatrixGenerationRequest,
    TradeoffMatrixGenerationService,
)
from tests.stub_litellm_client import StubLiteLLMClient


class StubSearchProvider:
    provider_name = "stub-search"

    def __init__(self, documents_by_query: dict[str, list[tuple[str, str]]]) -> None:
        self.documents_by_query = documents_by_query

    def search(self, *, query: str, max_results: int):
        from app.services.web_research import SearchResult

        return [
            SearchResult(
                title=title,
                url=url,
                snippet=f"Snippet for {title}",
                provider=self.provider_name,
                rank=index + 1,
                query=query,
            )
            for index, (title, url) in enumerate(self.documents_by_query.get(query, [])[:max_results])
        ]


class StubPageFetcher:
    def __init__(self, excerpts_by_url: dict[str, str]) -> None:
        self.excerpts_by_url = excerpts_by_url

    def fetch(self, *, url: str, query: str | None = None, rank: int | None = None):
        from datetime import UTC, datetime

        from app.services.web_research import RetrievedDocument

        return RetrievedDocument(
            title=f"Fetched {url}",
            url=url,
            excerpt=self.excerpts_by_url[url],
            query=query,
            provider="stub-search",
            rank=rank,
            retrieved_at=datetime.now(UTC),
        )


def _build_tradeoff_assessment_payload() -> GeneratedTradeoffAssessmentPayload:
    return GeneratedTradeoffAssessmentPayload(
        score=3.0,
        rationale="Balanced fit for this criterion given the current decision state.",
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
    assert '"context_summary"' in user_content
    assert '"criteria"' in user_content


def test_tradeoff_matrix_generation_validates_full_grid(
    db_session: Session,
    seeded_decision: str,
) -> None:
    decision = build_bootstrap_decision()
    options = build_bootstrap_options(seeded_decision)
    criteria = build_bootstrap_criteria(seeded_decision)
    incomplete = [
        TradeoffAssessmentCreate(
            criterion_id=criterion.id,
            option_id=option.id,
            score=3.0,
            rationale=f"Assessment for {criterion.name} vs {option.name}.",
        )
        for criterion in criteria
        for option in options
    ][:-1]
    stub = StubLiteLLMClient(responses={GeneratedTradeoffAssessmentPayload: _build_tradeoff_assessment_payload()})
    service = TradeoffMatrixGenerationService(db_session, client=stub)
    service._generate_assessments = lambda **_: incomplete  # type: ignore[method-assign]

    with pytest.raises(ValueError, match="every criterion-option pair"):
        service.generate_for_decision(
            seeded_decision,
            TradeoffMatrixGenerationRequest(),
        )


def test_tradeoff_matrix_generation_persists_stubbed_response(
    db_session: Session,
    seeded_decision: str,
) -> None:
    stub = StubLiteLLMClient(
        responses={GeneratedTradeoffAssessmentPayload: _build_tradeoff_assessment_payload()},
        model="stub-tradeoffs",
    )
    service = TradeoffMatrixGenerationService(db_session, client=stub)

    response = service.generate_for_decision(
        seeded_decision,
        TradeoffMatrixGenerationRequest(),
    )

    assert response.matrix.model == "stub-tradeoffs"
    assert len(response.matrix.assessments) == 12
    assert "Weighted scoring currently favors" in response.matrix.summary
    assert len(stub.calls) == 12
    assert stub.calls[0]["response_model"] is GeneratedTradeoffAssessmentPayload


def test_tradeoff_matrix_generation_retries_only_inconsistent_cell(
    db_session: Session,
    seeded_decision: str,
) -> None:
    stub = StubLiteLLMClient(
        responses={
            GeneratedTradeoffAssessmentPayload: [
                GeneratedTradeoffAssessmentPayload(
                    score=5.0,
                    rationale="This option contradicts the criterion and is not supported.",
                ),
                GeneratedTradeoffAssessmentPayload(
                    score=1.0,
                    rationale="This option conflicts with the criterion, so it is a poor fit.",
                ),
            ]
        },
        model="stub-tradeoffs",
    )
    service = TradeoffMatrixGenerationService(db_session, client=stub)

    assessment = service._generate_consistent_assessment(
        compact_context=CompactDecisionContext(
            question="Can the platform support this?",
            decision_type=DecisionType.FACTUAL_VERIFICATION,
            known_facts=[],
            options=[],
            criteria=[],
            critical_assumptions=[],
            evidence_summary=[],
        ),
        criterion_snapshot={
            "criterion_id": "criterion-1",
            "name": "Technical Feasibility",
            "weight": 0.5,
            "measurement_type": "boolean",
            "description": "Tests whether the option is feasible.",
        },
        option_snapshot={
            "option_id": "option-1",
            "name": "Option A",
            "description": "Option A",
        },
        factual_verification=None,
    )

    assert assessment.score == 1.0
    assert len(stub.calls) == 2


def test_criteria_generation_replaces_existing_set(
    db_session: Session,
    seeded_decision: str,
    minimal_criteria_payload: GeneratedCriteriaPayload,
) -> None:
    stub = StubLiteLLMClient(
        responses={GeneratedCriteriaPayload: minimal_criteria_payload},
        model="stub-criteria",
    )
    service = CriteriaGenerationService(db_session, client=stub)

    response = service.generate_for_decision(
        seeded_decision,
        CriteriaGenerationRequest(count=2, replace_existing=True),
    )

    assert response.model == "stub-criteria"
    assert response.replaced_existing is True
    assert len(response.criteria) == 2
    assert abs(sum(criterion.weight for criterion in response.criteria) - 1.0) < 0.001
    assert stub.calls[0]["response_model"] is GeneratedCriteriaPayload
    assert "Generate exactly 2 criteria" in stub.calls[0]["messages"][1]["content"]


def test_evidence_generation_persists_stubbed_response(
    db_session: Session,
    seeded_decision: str,
    minimal_evidence_payload: dict[str, GeneratedEvidencePayload | ReviewedEvidencePayload],
) -> None:
    stub = StubLiteLLMClient(
        responses={
            EvidenceResearchPlan: EvidenceResearchPlan(
                gaps=["Validate external benchmark claims."],
                queries=[
                    PlannedResearchQuery(
                        query="managed service database SLA comparison",
                        reason="Need current reliability and support posture across options.",
                    )
                ],
                target_urls=[],
            ),
            GeneratedEvidencePayload: minimal_evidence_payload["generated"],
            ReviewedEvidencePayload: minimal_evidence_payload["reviewed"],
        },
        model="stub-evidence",
    )
    service = EvidenceGenerationService(
        db_session,
        client=stub,
        search_provider=StubSearchProvider(
            {
                "managed service database SLA comparison": [
                    ("Vendor SLA", "https://example.com/vendor-sla"),
                    ("TCO analysis", "https://example.com/tco-analysis"),
                ]
            }
        ),
        page_fetcher=StubPageFetcher(
            {
                "https://example.com/vendor-sla": "The provider documents uptime commitments and maintenance windows.",
                "https://example.com/tco-analysis": "The article compares infrastructure, licensing, and staffing costs over three years.",
            }
        ),
    )

    response = service.generate_for_decision(
        seeded_decision,
        EvidenceGenerationRequest(
            count=2,
            research_focus="managed hosting maturity and TCO",
            allow_web_search=True,
        ),
    )

    assert response.model == "stub-evidence"
    assert response.replaced_existing is False
    assert response.agents_run == ["planner", "researcher", "synthesizer", "critic"]
    assert response.web_sources_consulted == 2
    assert len(response.evidence) == 2
    assert response.evidence[0].source_url == "https://example.com/vendor-sla"
    assert stub.calls[0]["response_model"] is EvidenceResearchPlan
    assert stub.calls[1]["response_model"] is GeneratedEvidencePayload
    assert stub.calls[2]["response_model"] is ReviewedEvidencePayload
    assert "Generate exactly 2 evidence items" in stub.calls[1]["messages"][1]["content"]


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
            responses={GeneratedTradeoffAssessmentPayload: _build_tradeoff_assessment_payload()},
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
            responses={GeneratedTradeoffAssessmentPayload: _build_tradeoff_assessment_payload()},
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
