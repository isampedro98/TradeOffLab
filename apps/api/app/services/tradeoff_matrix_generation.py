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


class GeneratedTradeoffAssessmentPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=1.0, le=5.0)
    rationale: str = Field(max_length=180)


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

        generated_assessments = self._generate_assessments(
            decision=decision,
            options=options,
            criteria=criteria,
            assumptions=assumptions,
        )
        expected_pairs = {(criterion.id, option.id) for criterion in criteria for option in options}
        returned_pairs = {
            (assessment.criterion_id, assessment.option_id) for assessment in generated_assessments
        }
        if returned_pairs != expected_pairs:
            raise ValueError(
                "Generated tradeoff matrix did not cover every criterion-option pair exactly once."
            )

        matrix = self.tradeoff_matrix_repository.replace_for_decision(
            decision_id,
            TradeoffMatrixReplace(
                summary=self._build_summary(
                    options=options,
                    criteria=criteria,
                    assessments=generated_assessments,
                ),
                scoring_scale_label="1-5 fit score (5 = strongest fit)",
                provider="litellm",
                model=self.client.model,
                assessments=generated_assessments,
            ),
        )
        return TradeoffMatrixGenerationResponse(
            replaced_existing=existing_matrix is not None,
            matrix=matrix,
        )

    def _generate_assessments(
        self,
        *,
        decision: Decision,
        options: list[Option],
        criteria: list[Criterion],
        assumptions: list[Assumption],
    ) -> list[TradeoffAssessmentCreate]:
        decision_snapshot = {
            "decision": {
                "title": decision.title,
                "question": _truncate_text(decision.question, limit=160),
                "context_summary": _truncate_text(decision.context, limit=160),
            },
            "assumptions": [
                {
                    "statement": _truncate_text(assumption.statement, limit=70),
                    "confidence": assumption.confidence.value,
                }
                for assumption in assumptions[:3]
            ],
        }
        generated_assessments: list[TradeoffAssessmentCreate] = []
        for criterion in criteria:
            criterion_snapshot = {
                "criterion_id": criterion.id,
                "name": criterion.name,
                "weight": criterion.weight,
                "measurement_type": criterion.measurement_type.value,
                "description": _truncate_text(criterion.description, limit=80),
            }
            for option in options:
                option_snapshot = {
                    "option_id": option.id,
                    "name": option.name,
                    "description": _truncate_text(option.description, limit=80),
                }
                payload = self._generate_assessment_payload(
                    decision_snapshot=decision_snapshot,
                    criterion_snapshot=criterion_snapshot,
                    option_snapshot=option_snapshot,
                )
                generated_assessments.append(
                    TradeoffAssessmentCreate(
                        criterion_id=criterion.id,
                        option_id=option.id,
                        score=payload.score,
                        rationale=payload.rationale,
                    )
                )
        return generated_assessments

    def _generate_assessment_payload(
        self,
        *,
        decision_snapshot: dict[str, object],
        criterion_snapshot: dict[str, object],
        option_snapshot: dict[str, object],
    ) -> GeneratedTradeoffAssessmentPayload:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are generating one structured tradeoff assessment for TradeOffLab. "
                    "Return only valid JSON. "
                    "Score on a 1 to 5 scale where 5 is strongest fit. "
                    "Write one short rationale sentence of 8 to 18 words."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Assess this option against this criterion. "
                    "Use only the provided decision state. "
                    "Do not mention missing evidence. "
                    "Be direct and concise.\n\n"
                    f"{json.dumps({'decision': decision_snapshot, 'criterion': criterion_snapshot, 'option': option_snapshot}, indent=2)}"
                ),
            },
        ]

        return self.client.generate_structured(
            messages=messages,
            response_model=GeneratedTradeoffAssessmentPayload,
            temperature=0.1,
            max_tokens=140,
        )

    def _build_summary(
        self,
        *,
        options: list[Option],
        criteria: list[Criterion],
        assessments: list[TradeoffAssessmentCreate],
    ) -> str:
        criterion_weights = {criterion.id: criterion.weight for criterion in criteria}
        option_names = {option.id: option.name for option in options}
        option_scores = {option.id: 0.0 for option in options}
        for assessment in assessments:
            option_scores[assessment.option_id] += assessment.score * criterion_weights.get(
                assessment.criterion_id, 0.0
            )
        ranked_options = sorted(option_scores.items(), key=lambda item: item[1], reverse=True)
        best_option_id, best_score = ranked_options[0]
        best_option_name = option_names[best_option_id]
        if len(ranked_options) == 1:
            return (
                f"Weighted scoring currently favors {best_option_name} with a composite score "
                f"of {best_score:.2f} on the configured criteria."
            )

        runner_up_option_id, runner_up_score = ranked_options[1]
        runner_up_option_name = option_names[runner_up_option_id]
        return (
            f"Weighted scoring currently favors {best_option_name} ({best_score:.2f}) over "
            f"{runner_up_option_name} ({runner_up_score:.2f}); review the per-criterion "
            "rationales before finalizing the decision."
        )


def _truncate_text(value: str, *, limit: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."
