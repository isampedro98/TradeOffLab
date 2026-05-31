import json

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.domain.adversarial_review import (
    AdversarialReview,
    AdversarialReviewFindingCreate,
    AdversarialReviewReplace,
    AdversarialReviewSeverity,
)
from app.domain.assumption import Assumption
from app.domain.criterion import Criterion
from app.domain.decision import Decision
from app.domain.option import Option
from app.domain.tradeoff_matrix import TradeoffMatrix
from app.persistence.adversarial_review_repository import AdversarialReviewRepository
from app.persistence.assumption_repository import AssumptionRepository
from app.persistence.criterion_repository import CriterionRepository
from app.persistence.decision_repository import DecisionRepository
from app.persistence.option_repository import OptionRepository
from app.persistence.tradeoff_matrix_repository import TradeoffMatrixRepository
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
        self.client = client or LiteLLMClient()
        self.adversarial_review_repository = AdversarialReviewRepository(session)
        self.assumption_repository = AssumptionRepository(session)
        self.criterion_repository = CriterionRepository(session)
        self.decision_repository = DecisionRepository(session)
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
        tradeoff_matrix: TradeoffMatrix,
    ) -> GeneratedAdversarialReviewPayload:
        decision_snapshot = {
            "decision": decision.model_dump(mode="json"),
            "options": [option.model_dump(mode="json") for option in options],
            "criteria": [criterion.model_dump(mode="json") for criterion in criteria],
            "assumptions": [assumption.model_dump(mode="json") for assumption in assumptions],
            "tradeoff_matrix": tradeoff_matrix.model_dump(mode="json"),
        }

        messages = [
            {
                "role": "system",
                "content": (
                    "You are generating a structured adversarial review for TradeOffLab. "
                    "Critique the current decision state and tradeoff matrix. "
                    "Surface the strongest risks, missing evidence, weak assumptions, "
                    "and ways the current analysis could be wrong. "
                    "Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Generate an adversarial review for this decision. "
                    "Return 3 to 5 findings. Keep each finding concrete, criticizable, "
                    "and directly tied to the provided state.\n\n"
                    f"{json.dumps(decision_snapshot, indent=2)}"
                ),
            },
        ]

        return self.client.generate_structured(
            messages=messages,
            response_model=GeneratedAdversarialReviewPayload,
        )
