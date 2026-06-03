import json
from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.assumption import Assumption
from app.domain.criterion import Criterion
from app.domain.decision import Decision, DecisionType
from app.domain.evidence import Evidence
from app.domain.option import Option
from app.domain.recommendation_memo import RecommendationConfidence
from app.domain.tradeoff_matrix import (
    TradeoffAssessmentCreate,
    TradeoffMatrix,
    TradeoffMatrixReplace,
)
from app.persistence.assumption_repository import AssumptionRepository
from app.persistence.criterion_repository import CriterionRepository
from app.persistence.decision_repository import DecisionRepository
from app.persistence.evidence_repository import EvidenceRepository
from app.persistence.option_repository import OptionRepository
from app.persistence.tradeoff_matrix_repository import TradeoffMatrixRepository
from app.services.decision_context import CompactDecisionContext, build_compact_decision_context
from app.services.litellm_client import LiteLLMClient


NEGATIVE_RATIONALE_TERMS = (
    "contradicts",
    "infeasible",
    "not supported",
    "conflicts with",
    "cannot",
    "not feasible",
    "unsupported",
    "blocks",
    "prevents",
)
POSITIVE_RATIONALE_TERMS = (
    "strong fit",
    "aligns well",
    "supports",
    "well suited",
    "good fit",
    "satisfies",
    "meets",
    "feasible",
)


class TradeoffMatrixGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    replace_existing: bool = True


class GeneratedTradeoffAssessmentPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=1.0, le=5.0)
    rationale: str = Field(max_length=180)


class FactualVerificationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supported_option_id: str | None = None
    confidence: RecommendationConfidence
    rationale: str = Field(max_length=220)
    conditions: list[str] = Field(default_factory=list, max_length=4)
    risks: list[str] = Field(default_factory=list, max_length=4)


class GeneratedTradeoffSelfCheckPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corrections: list[TradeoffAssessmentCreate] = Field(default_factory=list, max_length=8)


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
        self.client = client or LiteLLMClient(
            timeout_seconds=settings.litellm_timeout_tradeoff_matrix_seconds
        )
        self.assumption_repository = AssumptionRepository(session)
        self.criterion_repository = CriterionRepository(session)
        self.decision_repository = DecisionRepository(session)
        self.evidence_repository = EvidenceRepository(session)
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
        evidence = self.evidence_repository.list_for_decision(decision_id)

        if not options:
            raise ValueError("Tradeoff matrix generation requires at least one option.")
        if not criteria:
            raise ValueError("Tradeoff matrix generation requires at least one criterion.")
        if not assumptions:
            raise ValueError("Tradeoff matrix generation requires at least one assumption.")

        existing_matrix = self.tradeoff_matrix_repository.get_for_decision(decision_id)
        compact_context = build_compact_decision_context(
            decision=decision,
            options=options,
            criteria=criteria,
            assumptions=assumptions,
            evidence=evidence,
        )
        factual_verification = None
        if compact_context.decision_type == DecisionType.FACTUAL_VERIFICATION:
            factual_verification = self._generate_factual_verification(
                compact_context=compact_context,
                options=options,
            )

        generated_assessments = self._generate_assessments(
            compact_context=compact_context,
            decision=decision,
            options=options,
            criteria=criteria,
            factual_verification=factual_verification,
        )
        if settings.tradeoff_matrix_self_check_enabled:
            generated_assessments = self._self_check_assessments(
                compact_context=compact_context,
                options=options,
                criteria=criteria,
                assessments=generated_assessments,
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
                    compact_context=compact_context,
                    options=options,
                    criteria=criteria,
                    assessments=generated_assessments,
                    factual_verification=factual_verification,
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
        compact_context: CompactDecisionContext,
        decision: Decision,
        options: list[Option],
        criteria: list[Criterion],
        factual_verification: FactualVerificationPayload | None,
    ) -> list[TradeoffAssessmentCreate]:
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
                assessment_payload = self._generate_consistent_assessment(
                    compact_context=compact_context,
                    criterion_snapshot=criterion_snapshot,
                    option_snapshot=option_snapshot,
                    factual_verification=factual_verification,
                )
                generated_assessments.append(
                    TradeoffAssessmentCreate(
                        criterion_id=criterion.id,
                        option_id=option.id,
                        score=assessment_payload.score,
                        rationale=assessment_payload.rationale,
                    )
                )
        return generated_assessments

    def _generate_consistent_assessment(
        self,
        *,
        compact_context: CompactDecisionContext,
        criterion_snapshot: dict[str, object],
        option_snapshot: dict[str, object],
        factual_verification: FactualVerificationPayload | None,
    ) -> GeneratedTradeoffAssessmentPayload:
        payload = self._generate_assessment_payload(
            compact_context=compact_context,
            criterion_snapshot=criterion_snapshot,
            option_snapshot=option_snapshot,
            factual_verification=factual_verification,
        )
        consistency_issues = _find_assessment_consistency_issues(payload)

        retries = 0
        while consistency_issues and retries < settings.tradeoff_matrix_retry_limit:
            payload = self._retry_assessment_payload(
                compact_context=compact_context,
                criterion_snapshot=criterion_snapshot,
                option_snapshot=option_snapshot,
                factual_verification=factual_verification,
                previous_payload=payload,
                consistency_issues=consistency_issues,
            )
            consistency_issues = _find_assessment_consistency_issues(payload)
            retries += 1
        return payload

    def _generate_assessment_payload(
        self,
        *,
        compact_context: CompactDecisionContext,
        criterion_snapshot: dict[str, object],
        option_snapshot: dict[str, object],
        factual_verification: FactualVerificationPayload | None,
    ) -> GeneratedTradeoffAssessmentPayload:
        context_payload = {
            "compact_context": compact_context.model_dump(mode="json"),
            "criterion": criterion_snapshot,
            "option": option_snapshot,
        }
        if factual_verification is not None:
            context_payload["factual_verification"] = factual_verification.model_dump(mode="json")

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
                    "Use only the provided compact decision state. "
                    "If a factual_verification block is present, use it as the primary grounding. "
                    "Be direct and concise.\n\n"
                    f"{json.dumps(context_payload, indent=2)}"
                ),
            },
        ]

        return self.client.generate_structured(
            messages=messages,
            response_model=GeneratedTradeoffAssessmentPayload,
            temperature=0.1,
            max_tokens=140,
            timeout_seconds=settings.litellm_timeout_tradeoff_matrix_seconds,
        )

    def _retry_assessment_payload(
        self,
        *,
        compact_context: CompactDecisionContext,
        criterion_snapshot: dict[str, object],
        option_snapshot: dict[str, object],
        factual_verification: FactualVerificationPayload | None,
        previous_payload: GeneratedTradeoffAssessmentPayload,
        consistency_issues: list[str],
    ) -> GeneratedTradeoffAssessmentPayload:
        context_payload = {
            "compact_context": compact_context.model_dump(mode="json"),
            "criterion": criterion_snapshot,
            "option": option_snapshot,
            "previous_assessment": previous_payload.model_dump(mode="json"),
            "consistency_issues": consistency_issues,
        }
        if factual_verification is not None:
            context_payload["factual_verification"] = factual_verification.model_dump(mode="json")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are correcting one structured tradeoff assessment for TradeOffLab. "
                    "Return only valid JSON. Score on a 1 to 5 scale where 5 is strongest fit."
                ),
            },
            {
                "role": "user",
                "content": (
                    "The previous score and rationale were inconsistent. Re-evaluate the score. "
                    "If the rationale says the option contradicts the criterion, the score must be low. "
                    "If the rationale says the option strongly satisfies the criterion, the score must be high. "
                    "Return one corrected score and rationale only.\n\n"
                    f"{json.dumps(context_payload, indent=2)}"
                ),
            },
        ]
        return self.client.generate_structured(
            messages=messages,
            response_model=GeneratedTradeoffAssessmentPayload,
            temperature=0.0,
            max_tokens=140,
            timeout_seconds=settings.litellm_timeout_tradeoff_matrix_seconds,
        )

    def _generate_factual_verification(
        self,
        *,
        compact_context: CompactDecisionContext,
        options: list[Option],
    ) -> FactualVerificationPayload:
        option_snapshot = [
            {"option_id": option.id, "name": option.name} for option in options[:4]
        ]
        return self.client.generate_structured(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are generating a factual verification result for TradeOffLab. "
                        "Determine which option is best supported by the current compact context, "
                        "or return null if the result is uncertain. Return only valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "This decision is primarily factual. Produce a factual verification result "
                        "with confidence, conditions, risks, and a short rationale.\n\n"
                        f"{json.dumps({'compact_context': compact_context.model_dump(mode='json'), 'options': option_snapshot}, indent=2)}"
                    ),
                },
            ],
            response_model=FactualVerificationPayload,
            temperature=0.1,
            max_tokens=320,
            timeout_seconds=settings.litellm_timeout_tradeoff_matrix_seconds,
        )

    def _self_check_assessments(
        self,
        *,
        compact_context: CompactDecisionContext,
        options: list[Option],
        criteria: list[Criterion],
        assessments: list[TradeoffAssessmentCreate],
    ) -> list[TradeoffAssessmentCreate]:
        option_names = {option.id: option.name for option in options}
        criterion_names = {criterion.id: criterion.name for criterion in criteria}
        table_snapshot = [
            {
                "criterion_id": assessment.criterion_id,
                "criterion_name": criterion_names.get(
                    assessment.criterion_id, assessment.criterion_id
                ),
                "option_id": assessment.option_id,
                "option_name": option_names.get(assessment.option_id, assessment.option_id),
                "score": assessment.score,
                "rationale": assessment.rationale,
            }
            for assessment in assessments
        ]
        payload = self.client.generate_structured(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are reviewing a tradeoff scoring table for inconsistencies. "
                        "Return only the corrected cells, or an empty list if no corrections are needed. "
                        "Return only valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Review the scoring table. Identify any score/rationale inconsistencies and correct them. "
                        "Only return corrections for cells that should change.\n\n"
                        f"{json.dumps({'compact_context': compact_context.model_dump(mode='json'), 'assessment_table': table_snapshot}, indent=2)}"
                    ),
                },
            ],
            response_model=GeneratedTradeoffSelfCheckPayload,
            temperature=0.0,
            max_tokens=320,
            timeout_seconds=settings.litellm_timeout_tradeoff_self_check_seconds,
        )
        if not payload.corrections:
            return assessments

        assessment_map = {
            (assessment.criterion_id, assessment.option_id): assessment for assessment in assessments
        }
        for correction in payload.corrections:
            consistency_issues = _find_assessment_consistency_issues(correction)
            corrected_assessment = correction
            if consistency_issues:
                corrected_payload = self._retry_assessment_payload(
                    compact_context=compact_context,
                    criterion_snapshot={
                        "criterion_id": correction.criterion_id,
                        "name": criterion_names.get(correction.criterion_id, correction.criterion_id),
                    },
                    option_snapshot={
                        "option_id": correction.option_id,
                        "name": option_names.get(correction.option_id, correction.option_id),
                    },
                    factual_verification=None,
                    previous_payload=GeneratedTradeoffAssessmentPayload(
                        score=correction.score,
                        rationale=correction.rationale,
                    ),
                    consistency_issues=consistency_issues,
                )
                corrected_assessment = TradeoffAssessmentCreate(
                    criterion_id=correction.criterion_id,
                    option_id=correction.option_id,
                    score=corrected_payload.score,
                    rationale=corrected_payload.rationale,
                )
            assessment_map[(correction.criterion_id, correction.option_id)] = corrected_assessment
        return list(assessment_map.values())

    def _build_summary(
        self,
        *,
        compact_context: CompactDecisionContext,
        options: list[Option],
        criteria: list[Criterion],
        assessments: list[TradeoffAssessmentCreate],
        factual_verification: FactualVerificationPayload | None,
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

        summary_prefix = ""
        if factual_verification is not None and factual_verification.supported_option_id:
            supported_name = option_names.get(
                factual_verification.supported_option_id,
                factual_verification.supported_option_id,
            )
            summary_prefix = (
                f"Factual verification currently supports {supported_name} with "
                f"{factual_verification.confidence.value} confidence. "
            )

        if len(ranked_options) == 1:
            return (
                f"{summary_prefix}Weighted scoring currently favors {best_option_name} with a "
                f"composite score of {best_score:.2f} on the configured criteria."
            ).strip()

        runner_up_option_id, runner_up_score = ranked_options[1]
        runner_up_option_name = option_names[runner_up_option_id]
        decision_note = ""
        if compact_context.decision_type == DecisionType.FACTUAL_VERIFICATION:
            decision_note = " This matrix should be read as a factual verification aid, not a symmetric strategic tradeoff."
        return (
            f"{summary_prefix}Weighted scoring currently favors {best_option_name} ({best_score:.2f}) over "
            f"{runner_up_option_name} ({runner_up_score:.2f}); review the per-criterion rationales before "
            f"finalizing the decision.{decision_note}"
        ).strip()


def _find_assessment_consistency_issues(
    assessment: GeneratedTradeoffAssessmentPayload | TradeoffAssessmentCreate,
) -> list[str]:
    rationale = assessment.rationale.lower()
    issues: list[str] = []
    if assessment.score >= 4 and _contains_any(rationale, NEGATIVE_RATIONALE_TERMS):
        issues.append("High score conflicts with a negative rationale.")
    if assessment.score <= 2 and _contains_any(rationale, POSITIVE_RATIONALE_TERMS):
        issues.append("Low score conflicts with a strongly positive rationale.")
    return issues


def _contains_any(value: str, candidates: Iterable[str]) -> bool:
    return any(candidate in value for candidate in candidates)


def _truncate_text(value: str, *, limit: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."
