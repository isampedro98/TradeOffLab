import json

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.domain.assumption import Assumption
from app.domain.criterion import Criterion
from app.domain.decision import Decision
from app.domain.option import Option
from app.domain.tradeoff_matrix import (
    TradeoffAssessmentCreate,
    TradeoffMatrix,
    TradeoffMatrixReplace,
)
from app.persistence.assumption_repository import AssumptionRepository
from app.persistence.criterion_repository import CriterionRepository
from app.persistence.decision_repository import DecisionRepository
from app.persistence.option_repository import OptionRepository
from app.persistence.tradeoff_matrix_repository import TradeoffMatrixRepository
from app.services.litellm_client import LiteLLMClient


class TradeoffMatrixGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    replace_existing: bool = True


class GeneratedTradeoffMatrixPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    scoring_scale_label: str
    assessments: list[TradeoffAssessmentCreate]


class TradeoffMatrixGenerationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    replaced_existing: bool
    matrix: TradeoffMatrix


class TradeoffMatrixGenerationService:
    def __init__(
        self,
        session: Session,
        *,
        client: LiteLLMClient | None = None,
    ) -> None:
        self.session = session
        self.client = client or LiteLLMClient()
        self.assumption_repository = AssumptionRepository(session)
        self.criterion_repository = CriterionRepository(session)
        self.decision_repository = DecisionRepository(session)
        self.option_repository = OptionRepository(session)
        self.tradeoff_matrix_repository = TradeoffMatrixRepository(session)

    def generate_for_decision(
        self,
        decision_id: str,
        request: TradeoffMatrixGenerationRequest,
    ) -> TradeoffMatrixGenerationResponse:
        decision = self.decision_repository.get(decision_id)
        if decision is None:
            raise ValueError(f"Decision '{decision_id}' was not found.")

        options = self.option_repository.list_for_decision(decision_id)
        criteria = self.criterion_repository.list_for_decision(decision_id)
        assumptions = self.assumption_repository.list_for_decision(decision_id)

        if not options:
            raise ValueError("Tradeoff matrix generation requires at least one option.")
        if not criteria:
            raise ValueError("Tradeoff matrix generation requires at least one criterion.")
        if not assumptions:
            raise ValueError("Tradeoff matrix generation requires at least one assumption.")

        existing_matrix = self.tradeoff_matrix_repository.get_for_decision(decision_id)

        generated = self._generate_payload(
            decision=decision,
            options=options,
            criteria=criteria,
            assumptions=assumptions,
        )
        expected_pairs = {(criterion.id, option.id) for criterion in criteria for option in options}
        returned_pairs = {
            (assessment.criterion_id, assessment.option_id)
            for assessment in generated.assessments
        }
        if returned_pairs != expected_pairs:
            raise ValueError(
                "Generated tradeoff matrix did not cover every criterion-option pair exactly once."
            )

        matrix = self.tradeoff_matrix_repository.replace_for_decision(
            decision_id,
            TradeoffMatrixReplace(
                summary=generated.summary,
                scoring_scale_label=generated.scoring_scale_label,
                provider="litellm",
                model=self.client.model,
                assessments=generated.assessments,
            ),
        )
        return TradeoffMatrixGenerationResponse(
            replaced_existing=existing_matrix is not None,
            matrix=matrix,
        )

    def _generate_payload(
        self,
        *,
        decision: Decision,
        options: list[Option],
        criteria: list[Criterion],
        assumptions: list[Assumption],
    ) -> GeneratedTradeoffMatrixPayload:
        decision_snapshot = {
            "decision": decision.model_dump(mode="json"),
            "options": [option.model_dump(mode="json") for option in options],
            "criteria": [criterion.model_dump(mode="json") for criterion in criteria],
            "assumptions": [assumption.model_dump(mode="json") for assumption in assumptions],
        }

        messages = [
            {
                "role": "system",
                "content": (
                    "You are generating a structured tradeoff matrix for TradeOffLab. "
                    "Return one assessment for every criterion-option pair. "
                    "Scores must use a 1 to 5 scale where 5 is strongest fit. "
                    "Keep rationales concise, explicit, and grounded in the provided decision state. "
                    "Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Generate a tradeoff matrix for this decision. "
                    "Assess every option against every criterion exactly once.\n\n"
                    f"{json.dumps(decision_snapshot, indent=2)}"
                ),
            },
        ]

        return self.client.generate_structured(
            messages=messages,
            response_model=GeneratedTradeoffMatrixPayload,
        )
