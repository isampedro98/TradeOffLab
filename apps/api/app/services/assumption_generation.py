import json

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.config import settings
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

    count: int = Field(default=4, ge=1, le=7)
    replace_existing: bool = False
    assumption_ids: list[str] = Field(default_factory=list, max_length=7)


class GeneratedAssumptionsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assumptions: list[AssumptionCreate] = Field(min_length=1, max_length=7)


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
        self.client = client or LiteLLMClient(
            timeout_seconds=settings.litellm_timeout_assumptions_seconds
        )
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

        existing_assumptions = self.assumption_repository.list_for_decision(decision_id)
        selected_assumptions = [
            assumption
            for assumption in existing_assumptions
            if assumption.id in set(request.assumption_ids)
        ]
        if request.assumption_ids and len(selected_assumptions) != len(request.assumption_ids):
            raise ValueError(
                "One or more selected assumptions could not be found for this decision."
            )

        generation_count = len(request.assumption_ids) if request.assumption_ids else request.count
        generated = self._generate_payload(
            decision=decision,
            options=options,
            criteria=criteria,
            count=generation_count,
            existing_assumptions=existing_assumptions,
            selected_assumptions=selected_assumptions,
        )

        if request.assumption_ids:
            assumptions = self.assumption_repository.replace_selected(
                decision_id,
                request.assumption_ids,
                generated.assumptions,
            )
            replaced_existing = True
        elif request.replace_existing:
            self.assumption_repository.replace_for_decision(
                decision_id,
                generated.assumptions,
            )
            assumptions = self.assumption_repository.list_for_decision(decision_id)
            replaced_existing = True
        else:
            self.assumption_repository.create_many(
                decision_id,
                generated.assumptions,
            )
            assumptions = self.assumption_repository.list_for_decision(decision_id)
            replaced_existing = False

        return AssumptionGenerationResponse(
            decision_id=decision_id,
            replaced_existing=replaced_existing,
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
        existing_assumptions: list[Assumption],
        selected_assumptions: list[Assumption],
    ) -> GeneratedAssumptionsPayload:
        base_messages = self._build_messages(
            decision=decision,
            options=options,
            criteria=criteria,
            count=count,
            existing_assumptions=existing_assumptions,
            selected_assumptions=selected_assumptions,
        )

        return self.client.generate_structured(
            messages=base_messages,
            response_model=GeneratedAssumptionsPayload,
            temperature=0.1,
            max_tokens=700,
        )

    @staticmethod
    def _build_messages(
        *,
        decision: Decision,
        options: list[Option],
        criteria: list[Criterion],
        count: int,
        existing_assumptions: list[Assumption],
        selected_assumptions: list[Assumption],
    ) -> list[dict[str, str]]:
        decision_snapshot = {
            "decision": {
                "title": decision.title,
                "decision_brief": _truncate_text(decision.decision_brief, limit=180),
                "question": _truncate_text(decision.question, limit=220),
                "context_summary": _truncate_text(decision.context, limit=320),
            },
            "options": [
                {
                    "name": option.name,
                    "description": _truncate_text(option.description, limit=120),
                }
                for option in options
            ],
            "criteria": [
                {
                    "name": criterion.name,
                    "weight": criterion.weight,
                    "measurement_type": criterion.measurement_type.value,
                    "description": _truncate_text(criterion.description, limit=110),
                }
                for criterion in criteria
            ],
            "existing_assumptions": [
                {
                    "statement": _truncate_text(assumption.statement, limit=140),
                    "confidence": assumption.confidence.value,
                }
                for assumption in existing_assumptions[:7]
            ],
        }

        user_instruction = (
            f"Generate exactly {count} assumptions for this decision. "
            "Each assumption must include statement, confidence, impact_if_false, "
            "and validation_method. Keep them concrete, short, and testable. "
            "Use confidence only from: low, medium, high.\n\n"
        )
        if selected_assumptions:
            user_instruction = (
                f"Regenerate exactly {count} replacement assumptions for this decision. "
                "Only replace the selected assumptions. Keep the overall set diverse, "
                "avoid duplicating the preserved assumptions, and return only the new replacement assumptions.\n\n"
                f"Selected assumptions to replace:\n{json.dumps([_serialize_assumption(assumption) for assumption in selected_assumptions], indent=2)}\n\n"
            )

        return [
            {
                "role": "system",
                "content": (
                    "You are generating structured assumptions for TradeOffLab, an AI-assisted "
                    "decision engineering workspace. Produce concise, criticizable assumptions "
                    "grounded in the supplied decision state. Do not return markdown or commentary."
                ),
            },
            {
                "role": "user",
                "content": user_instruction + json.dumps(decision_snapshot, indent=2),
            },
        ]


def _serialize_assumption(assumption: Assumption) -> dict[str, str]:
    return {
        "statement": _truncate_text(assumption.statement, limit=140),
        "confidence": assumption.confidence.value,
        "impact_if_false": _truncate_text(assumption.impact_if_false, limit=160),
        "validation_method": _truncate_text(assumption.validation_method, limit=160),
    }


def _truncate_text(value: str, *, limit: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."
