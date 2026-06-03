import json

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.adversarial_review import (
    AdversarialReview,
    AdversarialReviewFindingCreate,
    AdversarialReviewReplace,
    AdversarialReviewSeverity,
)
from app.domain.assumption import Assumption
from app.domain.criterion import Criterion
from app.domain.decision import Decision
from app.domain.evidence import Evidence
from app.domain.option import Option
from app.domain.tradeoff_matrix import TradeoffMatrix
from app.persistence.adversarial_review_repository import AdversarialReviewRepository
from app.persistence.assumption_repository import AssumptionRepository
from app.persistence.criterion_repository import CriterionRepository
from app.persistence.decision_repository import DecisionRepository
from app.persistence.evidence_repository import EvidenceRepository
from app.persistence.option_repository import OptionRepository
from app.persistence.tradeoff_matrix_repository import TradeoffMatrixRepository
from app.services.decision_context import build_compact_decision_context
from app.services.litellm_client import LiteLLMClient


class AdversarialReviewGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    replace_existing: bool = True


class GeneratedAdversarialReviewPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    overall_risk: AdversarialReviewSeverity
    findings: list[AdversarialReviewFindingCreate]


class AdversarialReviewGenerationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    replaced_existing: bool
    review: AdversarialReview


class AdversarialReviewGenerationService:
    def __init__(
        self,
        session: Session,
        *,
        client: LiteLLMClient | None = None,
    ) -> None:
        self.session = session
        self.client = client or LiteLLMClient(
            timeout_seconds=settings.litellm_timeout_adversarial_review_seconds
        )
        self.adversarial_review_repository = AdversarialReviewRepository(session)
        self.assumption_repository = AssumptionRepository(session)
        self.criterion_repository = CriterionRepository(session)
        self.decision_repository = DecisionRepository(session)
        self.evidence_repository = EvidenceRepository(session)
        self.option_repository = OptionRepository(session)
        self.tradeoff_matrix_repository = TradeoffMatrixRepository(session)

    def generate_for_decision(
        self,
        decision_id: str,
        request: AdversarialReviewGenerationRequest,
    ) -> AdversarialReviewGenerationResponse:
        decision = self.decision_repository.get(decision_id)
        if decision is None:
            raise ValueError(f"Decision '{decision_id}' was not found.")

        options = self.option_repository.list_for_decision(decision_id)
        criteria = self.criterion_repository.list_for_decision(decision_id)
        assumptions = self.assumption_repository.list_for_decision(decision_id)
        evidence = self.evidence_repository.list_for_decision(decision_id)
        tradeoff_matrix = self.tradeoff_matrix_repository.get_for_decision(decision_id)

        if not options:
            raise ValueError("Adversarial review generation requires at least one option.")
        if not criteria:
            raise ValueError("Adversarial review generation requires at least one criterion.")
        if not assumptions:
            raise ValueError("Adversarial review generation requires at least one assumption.")
        if tradeoff_matrix is None:
            raise ValueError("Adversarial review generation requires a tradeoff matrix.")

        existing_review = self.adversarial_review_repository.get_for_decision(decision_id)
        generated = self._generate_payload(
            decision=decision,
            options=options,
            criteria=criteria,
            assumptions=assumptions,
            evidence=evidence,
            tradeoff_matrix=tradeoff_matrix,
        )
        review = self.adversarial_review_repository.replace_for_decision(
            decision_id,
            AdversarialReviewReplace(
                summary=generated.summary,
                overall_risk=generated.overall_risk,
                provider="litellm",
                model=self.client.model,
                findings=generated.findings,
            ),
        )
        return AdversarialReviewGenerationResponse(
            replaced_existing=existing_review is not None,
            review=review,
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
    ) -> GeneratedAdversarialReviewPayload:
        compact_context = build_compact_decision_context(
            decision=decision,
            options=options,
            criteria=criteria,
            assumptions=assumptions,
            evidence=evidence,
        )
        option_names = {option.id: option.name for option in options}
        criterion_names = {criterion.id: criterion.name for criterion in criteria}
        weighted_option_scores = _build_weighted_option_scores(
            tradeoff_matrix=tradeoff_matrix,
            criteria=criteria,
            option_names=option_names,
        )
        weakest_assessments = sorted(
            tradeoff_matrix.assessments,
            key=lambda assessment: (assessment.score, assessment.criterion_id, assessment.option_id),
        )[:3]
        decision_snapshot = {
            "compact_context": compact_context.model_dump(mode="json"),
            "tradeoff_matrix": {
                "summary": _truncate_text(tradeoff_matrix.summary, limit=160),
                "weighted_option_scores": weighted_option_scores,
                "weakest_assessments": [
                    {
                        "criterion": criterion_names.get(
                            assessment.criterion_id, assessment.criterion_id
                        ),
                        "option": option_names.get(assessment.option_id, assessment.option_id),
                        "score": assessment.score,
                    }
                    for assessment in weakest_assessments
                ],
            },
        }

        messages = [
            {
                "role": "system",
                "content": (
                    "You are generating a structured adversarial review for TradeOffLab. "
                    "Critique the current decision state and tradeoff matrix. "
                    "Surface the strongest risks, missing evidence, weak assumptions, "
                    "and ways the current analysis could be wrong. "
                    "Keep the summary short. Keep findings concrete and concise. "
                    "Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Generate an adversarial review for this decision. "
                    "Return exactly 3 findings. Keep each finding concrete, criticizable, "
                    "and directly tied to the provided state. Prefer short sentences and avoid repetition. "
                    "Focus on weak assumptions, missing validation, and failure modes in the current scoring.\n\n"
                    f"{json.dumps(decision_snapshot, indent=2)}"
                ),
            },
        ]

        return self.client.generate_structured(
            messages=messages,
            response_model=GeneratedAdversarialReviewPayload,
            temperature=0.1,
            max_tokens=450,
            timeout_seconds=settings.litellm_timeout_adversarial_review_seconds,
        )


def _build_weighted_option_scores(
    *,
    tradeoff_matrix: TradeoffMatrix,
    criteria: list[Criterion],
    option_names: dict[str, str],
) -> list[dict[str, object]]:
    criterion_weights = {criterion.id: criterion.weight for criterion in criteria}
    scores_by_option: dict[str, float] = {}
    for assessment in tradeoff_matrix.assessments:
        scores_by_option.setdefault(assessment.option_id, 0.0)
        scores_by_option[assessment.option_id] += assessment.score * criterion_weights.get(
            assessment.criterion_id, 0.0
        )
    ranked_scores = sorted(scores_by_option.items(), key=lambda item: item[1], reverse=True)
    return [
        {"option": option_names.get(option_id, option_id), "weighted_score": round(score, 2)}
        for option_id, score in ranked_scores
    ]


def _truncate_text(value: str, *, limit: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."
