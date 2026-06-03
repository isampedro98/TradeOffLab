import json

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.domain.criterion import Criterion, CriterionCreate
from app.domain.decision import Decision
from app.domain.option import Option
from app.persistence.criterion_repository import CriterionRepository
from app.persistence.decision_repository import DecisionRepository
from app.persistence.option_repository import OptionRepository
from app.services.litellm_client import LiteLLMClient


class CriteriaGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int = Field(default=5, ge=1, le=7)
    replace_existing: bool = True


class GeneratedCriteriaPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criteria: list[CriterionCreate] = Field(min_length=1, max_length=7)


class CriteriaGenerationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_id: str
    replaced_existing: bool
    model: str
    criteria: list[Criterion]


class CriteriaGenerationService:
    def __init__(
        self,
        session: Session,
        *,
        client: LiteLLMClient | None = None,
    ) -> None:
        self.session = session
        self.client = client or LiteLLMClient()
        self.criterion_repository = CriterionRepository(session)
        self.decision_repository = DecisionRepository(session)
        self.option_repository = OptionRepository(session)

    def generate_for_decision(
        self,
        decision_id: str,
        request: CriteriaGenerationRequest,
    ) -> CriteriaGenerationResponse:
        decision = self.decision_repository.get(decision_id)
        if decision is None:
            raise ValueError(f"Decision '{decision_id}' was not found.")

        options = self.option_repository.list_for_decision(decision_id)
        existing_criteria = self.criterion_repository.list_for_decision(decision_id)

        if existing_criteria and not request.replace_existing:
            raise ValueError(
                "Criteria generation must replace the current criteria set so weights remain coherent."
            )

        generated = self._generate_payload(
            decision=decision,
            options=options,
            existing_criteria=existing_criteria,
            count=request.count,
        )
        self._validate_generated_criteria(generated.criteria, expected_count=request.count)

        criteria = self.criterion_repository.replace_for_decision(
            decision_id,
            generated.criteria,
        )
        return CriteriaGenerationResponse(
            decision_id=decision_id,
            replaced_existing=bool(existing_criteria),
            model=self.client.model,
            criteria=criteria,
        )

    def _generate_payload(
        self,
        *,
        decision: Decision,
        options: list[Option],
        existing_criteria: list[Criterion],
        count: int,
    ) -> GeneratedCriteriaPayload:
        decision_snapshot = {
            "decision": decision.model_dump(mode="json"),
            "options": [option.model_dump(mode="json") for option in options],
            "existing_criteria": [
                criterion.model_dump(mode="json") for criterion in existing_criteria
            ],
        }

        messages = [
            {
                "role": "system",
                "content": (
                    "You are generating structured evaluation criteria for TradeOffLab. "
                    "Return a complete, non-overlapping criterion set for the current decision. "
                    "Each criterion must include name, description, weight, and measurement_type. "
                    "Weights must form a coherent full set. Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Generate exactly {count} criteria for this decision. "
                    "Treat the response as a complete replacement set. "
                    "Use measurement_type values only from: qualitative, numeric, boolean, ordinal. "
                    "Make criterion names distinct, descriptions concrete, and weights sum to 1.0.\n\n"
                    f"{json.dumps(decision_snapshot, indent=2)}"
                ),
            },
        ]

        return self.client.generate_structured(
            messages=messages,
            response_model=GeneratedCriteriaPayload,
        )

    @staticmethod
    def _validate_generated_criteria(
        criteria: list[CriterionCreate],
        *,
        expected_count: int,
    ) -> None:
        if len(criteria) != expected_count:
            raise ValueError(
                f"Generated criteria count mismatch: expected {expected_count}, received {len(criteria)}."
            )

        total_weight = sum(criterion.weight for criterion in criteria)
        if any(criterion.weight <= 0 for criterion in criteria):
            raise ValueError("Generated criteria weights must all be greater than zero.")
        if abs(total_weight - 1.0) > 0.05:
            raise ValueError("Generated criteria weights must sum to approximately 1.0.")

        normalized_names = {criterion.name.strip().lower() for criterion in criteria}
        if len(normalized_names) != len(criteria):
            raise ValueError("Generated criteria names must be unique.")
