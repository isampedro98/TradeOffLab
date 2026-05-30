import json

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.domain.assumption import Assumption, AssumptionCreate
from app.domain.criterion import Criterion
from app.domain.decision import Decision
from app.domain.option import Option
from app.persistence.assumption_repository import AssumptionRepository
from app.persistence.criterion_repository import CriterionRepository
from app.persistence.decision_repository import DecisionRepository
from app.persistence.option_repository import OptionRepository
from app.services.litellm_client import LiteLLMClient, LiteLLMError


class AssumptionGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int = Field(default=4, ge=3, le=7)
    replace_existing: bool = False


class GeneratedAssumptionsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assumptions: list[AssumptionCreate] = Field(min_length=3, max_length=7)


class AssumptionGenerationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_id: str
    replaced_existing: bool
    model: str
    assumptions: list[Assumption]


class AssumptionGenerationService:
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

    def generate_for_decision(
        self,
        decision_id: str,
        request: AssumptionGenerationRequest,
    ) -> AssumptionGenerationResponse:
        decision = self.decision_repository.get(decision_id)
        if decision is None:
            raise ValueError(f"Decision '{decision_id}' was not found.")

        options = self.option_repository.list_for_decision(decision_id)
        criteria = self.criterion_repository.list_for_decision(decision_id)

        if not options:
            raise ValueError("Assumption generation requires at least one option.")
        if not criteria:
            raise ValueError("Assumption generation requires at least one criterion.")

        generated = self._generate_payload(
            decision=decision,
            options=options,
            criteria=criteria,
            count=request.count,
        )

        if request.replace_existing:
            assumptions = self.assumption_repository.replace_for_decision(
                decision_id,
                generated.assumptions,
            )
        else:
            assumptions = self.assumption_repository.create_many(
                decision_id,
                generated.assumptions,
            )

        return AssumptionGenerationResponse(
            decision_id=decision_id,
            replaced_existing=request.replace_existing,
            model=self.client.model,
            assumptions=assumptions,
        )

    def _generate_payload(
        self,
        *,
        decision: Decision,
        options: list[Option],
        criteria: list[Criterion],
        count: int,
    ) -> GeneratedAssumptionsPayload:
        base_messages = self._build_messages(
            decision=decision,
            options=options,
            criteria=criteria,
            count=count,
        )

        return self.client.generate_structured(
            messages=base_messages,
            response_model=GeneratedAssumptionsPayload,
        )

    @staticmethod
    def _build_messages(
        *,
        decision: Decision,
        options: list[Option],
        criteria: list[Criterion],
        count: int,
    ) -> list[dict[str, str]]:
        decision_snapshot = {
            "decision": decision.model_dump(mode="json"),
            "options": [option.model_dump(mode="json") for option in options],
            "criteria": [criterion.model_dump(mode="json") for criterion in criteria],
        }

        return [
            {
                "role": "system",
                "content": (
                    "You are generating structured assumptions for TradeOffLab, an AI-assisted "
                    "decision engineering workspace. Produce concise, criticizable assumptions "
                    "grounded in the supplied decision state. Do not return markdown."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Generate exactly {count} assumptions for this decision. "
                    "Each assumption must include statement, confidence, impact_if_false, "
                    "and validation_method. Keep them concrete and testable.\n\n"
                    f"{json.dumps(decision_snapshot, indent=2)}"
                ),
            },
        ]
