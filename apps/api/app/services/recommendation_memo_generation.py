import json

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.adversarial_review import AdversarialReview
from app.domain.assumption import Assumption
from app.domain.criterion import Criterion
from app.domain.decision import Decision
from app.domain.evidence import Evidence
from app.domain.option import Option
from app.domain.recommendation_memo import (
    RecommendationConditionCreate,
    RecommendationConfidence,
    RecommendationMemo,
    RecommendationMemoReplace,
)
from app.domain.tradeoff_matrix import TradeoffMatrix
from app.persistence.adversarial_review_repository import AdversarialReviewRepository
from app.persistence.assumption_repository import AssumptionRepository
from app.persistence.criterion_repository import CriterionRepository
from app.persistence.decision_repository import DecisionRepository
from app.persistence.evidence_repository import EvidenceRepository
from app.persistence.option_repository import OptionRepository
from app.persistence.recommendation_memo_repository import RecommendationMemoRepository
from app.persistence.tradeoff_matrix_repository import TradeoffMatrixRepository
from app.services.decision_context import build_compact_decision_context
from app.services.litellm_client import LiteLLMClient


class RecommendationMemoGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    replace_existing: bool = True


class GeneratedRecommendationMemoPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommended_option_id: str
    fallback_option_id: str | None = None
    rationale: str
    confidence: RecommendationConfidence
    conditions: list[RecommendationConditionCreate]


class RecommendationMemoGenerationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    replaced_existing: bool
    memo: RecommendationMemo


class RecommendationMemoGenerationService:
    def __init__(
        self,
        session: Session,
        *,
        client: LiteLLMClient | None = None,
    ) -> None:
        self.session = session
        self.client = client or LiteLLMClient(
            timeout_seconds=settings.litellm_timeout_recommendation_memo_seconds
        )
        self.adversarial_review_repository = AdversarialReviewRepository(session)
        self.assumption_repository = AssumptionRepository(session)
        self.criterion_repository = CriterionRepository(session)
        self.decision_repository = DecisionRepository(session)
        self.evidence_repository = EvidenceRepository(session)
        self.option_repository = OptionRepository(session)
        self.recommendation_memo_repository = RecommendationMemoRepository(session)
        self.tradeoff_matrix_repository = TradeoffMatrixRepository(session)

    def generate_for_decision(
        self,
        decision_id: str,
        request: RecommendationMemoGenerationRequest,
    ) -> RecommendationMemoGenerationResponse:
        decision = self.decision_repository.get(decision_id)
        if decision is None:
            raise ValueError(f"Decision '{decision_id}' was not found.")

        options = self.option_repository.list_for_decision(decision_id)
        criteria = self.criterion_repository.list_for_decision(decision_id)
        assumptions = self.assumption_repository.list_for_decision(decision_id)
        evidence = self.evidence_repository.list_for_decision(decision_id)
        tradeoff_matrix = self.tradeoff_matrix_repository.get_for_decision(decision_id)
        adversarial_review = self.adversarial_review_repository.get_for_decision(decision_id)

        if not options:
            raise ValueError("Recommendation generation requires at least one option.")
        if not criteria:
            raise ValueError("Recommendation generation requires at least one criterion.")
        if not assumptions:
            raise ValueError("Recommendation generation requires at least one assumption.")
        if tradeoff_matrix is None:
            raise ValueError("Recommendation generation requires a tradeoff matrix.")
        if adversarial_review is None:
            raise ValueError("Recommendation generation requires an adversarial review.")

        existing_memo = self.recommendation_memo_repository.get_for_decision(decision_id)
        generated = self._generate_payload(
            decision=decision,
            options=options,
            criteria=criteria,
            assumptions=assumptions,
            evidence=evidence,
            tradeoff_matrix=tradeoff_matrix,
            adversarial_review=adversarial_review,
        )
        generated = self._apply_recommendation_safeguards(
            generated=generated,
            options=options,
            adversarial_review=adversarial_review,
        )

        option_ids = {option.id for option in options}
        if generated.recommended_option_id not in option_ids:
            raise ValueError("Recommendation memo selected an unknown recommended option.")
        if (
            generated.fallback_option_id is not None
            and generated.fallback_option_id not in option_ids
        ):
            raise ValueError("Recommendation memo selected an unknown fallback option.")
        if generated.fallback_option_id == generated.recommended_option_id:
            raise ValueError("Fallback option must differ from the recommended option.")

        memo = self.recommendation_memo_repository.replace_for_decision(
            decision_id,
            RecommendationMemoReplace(
                recommended_option_id=generated.recommended_option_id,
                fallback_option_id=generated.fallback_option_id,
                rationale=generated.rationale,
                confidence=generated.confidence,
                provider="litellm",
                model=self.client.model,
                conditions=generated.conditions,
            ),
        )
        return RecommendationMemoGenerationResponse(
            replaced_existing=existing_memo is not None,
            memo=memo,
        )

    def _generate_payload(
        self,
        *,
        decision: Decision,
        options: list[Option],
        criteria: list[Criterion],
        assumptions: list[Assumption],
        evidence: list[Evidence],
        tradeoff_matrix: TradeoffMatrix,
        adversarial_review: AdversarialReview,
    ) -> GeneratedRecommendationMemoPayload:
        compact_context = build_compact_decision_context(
            decision=decision,
            options=options,
            criteria=criteria,
            assumptions=assumptions,
            evidence=evidence,
        )
        decision_snapshot = {
            "compact_context": compact_context.model_dump(mode="json"),
            "options": [
                {
                    "option_id": option.id,
                    "name": option.name,
                    "description": _truncate_text(option.description, limit=70),
                }
                for option in options
            ],
            "criteria": [
                {
                    "criterion_id": criterion.id,
                    "name": criterion.name,
                    "weight": criterion.weight,
                }
                for criterion in criteria
            ],
            "assumptions": [
                {
                    "statement": _truncate_text(assumption.statement, limit=80),
                    "confidence": assumption.confidence.value,
                }
                for assumption in assumptions[:4]
            ],
            "tradeoff_matrix": {
                "summary": _truncate_text(tradeoff_matrix.summary, limit=220),
                "best_assessments": [
                    _serialize_assessment(assessment)
                    for assessment in sorted(
                        tradeoff_matrix.assessments,
                        key=lambda item: item.score,
                        reverse=True,
                    )[:4]
                ],
                "worst_assessments": [
                    _serialize_assessment(assessment)
                    for assessment in sorted(
                        tradeoff_matrix.assessments,
                        key=lambda item: item.score,
                    )[:4]
                ],
            },
            "adversarial_review": {
                "summary": _truncate_text(adversarial_review.summary, limit=220),
                "overall_risk": adversarial_review.overall_risk.value,
                "findings": [
                    {
                        "title": _truncate_text(finding.title, limit=60),
                        "severity": finding.severity.value,
                        "critique": _truncate_text(finding.critique, limit=90),
                        "consequence": _truncate_text(finding.consequence, limit=90),
                        "mitigation_test": _truncate_text(finding.mitigation_test, limit=90),
                    }
                    for finding in adversarial_review.findings[:3]
                ],
            },
        }

        messages = [
            {
                "role": "system",
                "content": (
                    "You are generating a structured recommendation memo for TradeOffLab. "
                    "Choose one recommended option, optionally one fallback option, explain the rationale, "
                    "and state the conditions under which the recommendation should hold. "
                    "Use the adversarial review to temper confidence and conditions. "
                    "Keep the rationale concise and the conditions specific. "
                    "Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Generate a recommendation memo for this decision. "
                    "Prefer concrete conditions and make the rationale traceable to the current decision state. "
                    "Keep output short and direct.\n\n"
                    f"{json.dumps(decision_snapshot, indent=2)}"
                ),
            },
        ]

        return self.client.generate_structured(
            messages=messages,
            response_model=GeneratedRecommendationMemoPayload,
            temperature=0.1,
            max_tokens=550,
            timeout_seconds=settings.litellm_timeout_recommendation_memo_seconds,
        )

    def _apply_recommendation_safeguards(
        self,
        *,
        generated: GeneratedRecommendationMemoPayload,
        options: list[Option],
        adversarial_review: AdversarialReview,
    ) -> GeneratedRecommendationMemoPayload:
        option_names = {option.id: option.name.lower() for option in options}
        recommended_name = option_names.get(generated.recommended_option_id, "")
        high_severity_findings = [
            finding
            for finding in adversarial_review.findings
            if finding.severity.value == "high"
            and recommended_name
            and recommended_name in " ".join(
                [finding.title.lower(), finding.critique.lower(), finding.consequence.lower()]
            )
        ]
        if len(high_severity_findings) < 2:
            return generated

        adjusted_confidence = generated.confidence
        if generated.confidence == RecommendationConfidence.HIGH:
            adjusted_confidence = RecommendationConfidence.MEDIUM
        elif generated.confidence == RecommendationConfidence.MEDIUM:
            adjusted_confidence = RecommendationConfidence.LOW

        conditions = list(generated.conditions)
        safeguard_statement = (
            "Recommendation requires explicit justification because multiple high-severity "
            "adversarial findings target the selected option."
        )
        if safeguard_statement not in {condition.statement for condition in conditions}:
            conditions.append(RecommendationConditionCreate(statement=safeguard_statement))

        return generated.model_copy(
            update={
                "confidence": adjusted_confidence,
                "conditions": conditions,
            }
        )


def _serialize_assessment(assessment: object) -> dict[str, object]:
    return {
        "criterion_id": getattr(assessment, "criterion_id"),
        "option_id": getattr(assessment, "option_id"),
        "score": getattr(assessment, "score"),
        "rationale": _truncate_text(getattr(assessment, "rationale"), limit=90),
    }


def _truncate_text(value: str, *, limit: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."
