from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.domain.adversarial_review import AdversarialReview
from app.domain.assumption import Assumption
from app.domain.criterion import Criterion
from app.domain.decision import Decision
from app.domain.evidence import Evidence
from app.domain.option import Option
from app.domain.recommendation_memo import RecommendationMemo
from app.domain.tradeoff_matrix import TradeoffMatrix
from app.persistence.adversarial_review_repository import AdversarialReviewRepository
from app.persistence.assumption_repository import AssumptionRepository
from app.persistence.criterion_repository import CriterionRepository
from app.persistence.decision_repository import DecisionRepository
from app.persistence.evidence_repository import EvidenceRepository
from app.persistence.option_repository import OptionRepository
from app.persistence.recommendation_memo_repository import RecommendationMemoRepository
from app.persistence.tradeoff_matrix_repository import TradeoffMatrixRepository


class DecisionDossierExport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Decision
    options: list[Option]
    criteria: list[Criterion]
    assumptions: list[Assumption]
    evidence: list[Evidence] = Field(default_factory=list)
    tradeoff_matrix: TradeoffMatrix | None = None
    adversarial_review: AdversarialReview | None = None
    recommendation_memo: RecommendationMemo | None = None


class DecisionExportService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.adversarial_review_repository = AdversarialReviewRepository(session)
        self.assumption_repository = AssumptionRepository(session)
        self.criterion_repository = CriterionRepository(session)
        self.decision_repository = DecisionRepository(session)
        self.evidence_repository = EvidenceRepository(session)
        self.option_repository = OptionRepository(session)
        self.recommendation_memo_repository = RecommendationMemoRepository(session)
        self.tradeoff_matrix_repository = TradeoffMatrixRepository(session)

    def build_dossier(self, decision_id: str) -> DecisionDossierExport:
        decision = self.decision_repository.get(decision_id)
        if decision is None:
            raise ValueError(f"Decision '{decision_id}' was not found.")

        return DecisionDossierExport(
            decision=decision,
            options=self.option_repository.list_for_decision(decision_id),
            criteria=self.criterion_repository.list_for_decision(decision_id),
            assumptions=self.assumption_repository.list_for_decision(decision_id),
            evidence=self.evidence_repository.list_for_decision(decision_id),
            tradeoff_matrix=self.tradeoff_matrix_repository.get_for_decision(decision_id),
            adversarial_review=self.adversarial_review_repository.get_for_decision(decision_id),
            recommendation_memo=self.recommendation_memo_repository.get_for_decision(
                decision_id
            ),
        )

    def build_markdown(self, decision_id: str) -> str:
        dossier = self.build_dossier(decision_id)
        decision = dossier.decision
        option_map = {option.id: option for option in dossier.options}
        criterion_map = {criterion.id: criterion for criterion in dossier.criteria}

        lines: list[str] = [
            f"# {decision.title}",
            "",
            f"**Decision Brief:** {decision.decision_brief}",
            "",
            f"**Question:** {decision.question}",
            "",
            "## Context",
            "",
            decision.context,
            "",
            "## Decision Metadata",
            "",
            f"- Decision ID: `{decision.id}`",
            f"- Type: `{decision.type.value}`",
            f"- Status: `{decision.status.value}`",
            f"- Created At: `{decision.created_at.isoformat()}`",
            f"- Updated At: `{decision.updated_at.isoformat()}`",
            "",
            "## Options",
            "",
        ]

        if dossier.options:
            for option in dossier.options:
                lines.extend(
                    [
                        f"### {option.name}",
                        "",
                        option.description,
                        "",
                    ]
                )
        else:
            lines.extend(["No options recorded yet.", ""])

        lines.extend(["## Criteria", ""])
        if dossier.criteria:
            for criterion in dossier.criteria:
                lines.extend(
                    [
                        f"### {criterion.name}",
                        "",
                        f"- Weight: `{criterion.weight}`",
                        f"- Measurement Type: `{criterion.measurement_type.value}`",
                        "",
                        criterion.description,
                        "",
                    ]
                )
        else:
            lines.extend(["No criteria recorded yet.", ""])

        lines.extend(["## Assumptions", ""])
        if dossier.assumptions:
            for assumption in dossier.assumptions:
                lines.extend(
                    [
                        f"### {assumption.statement}",
                        "",
                        f"- Confidence: `{assumption.confidence.value}`",
                        f"- Impact If False: {assumption.impact_if_false}",
                        f"- Validation Method: {assumption.validation_method}",
                        "",
                    ]
                )
        else:
            lines.extend(["No assumptions recorded yet.", ""])

        lines.extend(["## Evidence", ""])
        if dossier.evidence:
            for evidence in dossier.evidence:
                lines.extend(
                    [
                        f"### {evidence.title}",
                        "",
                        f"- Source: {evidence.source}",
                        "",
                        evidence.summary,
                        "",
                    ]
                )
        else:
            lines.extend(
                [
                    "No evidence recorded yet.",
                    "",
                ]
            )

        lines.extend(["## Tradeoff Matrix", ""])
        if dossier.tradeoff_matrix:
            lines.extend([dossier.tradeoff_matrix.summary, ""])
            for criterion in dossier.criteria:
                criterion_assessments = [
                    assessment
                    for assessment in dossier.tradeoff_matrix.assessments
                    if assessment.criterion_id == criterion.id
                ]
                if not criterion_assessments:
                    continue
                lines.extend([f"### {criterion.name}", ""])
                for assessment in criterion_assessments:
                    option = option_map.get(assessment.option_id)
                    lines.extend(
                        [
                            f"- **{option.name if option else assessment.option_id}**: score `{assessment.score}`. {assessment.rationale}",
                        ]
                    )
                lines.append("")
        else:
            lines.extend(["No tradeoff matrix generated yet.", ""])

        lines.extend(["## Adversarial Review", ""])
        if dossier.adversarial_review:
            lines.extend(
                [
                    dossier.adversarial_review.summary,
                    "",
                    f"- Overall Risk: `{dossier.adversarial_review.overall_risk.value}`",
                    "",
                ]
            )
            for finding in dossier.adversarial_review.findings:
                lines.extend(
                    [
                        f"### {finding.title}",
                        "",
                        f"- Severity: `{finding.severity.value}`",
                        f"- Critique: {finding.critique}",
                        f"- Consequence: {finding.consequence}",
                        f"- Mitigation Test: {finding.mitigation_test}",
                        "",
                    ]
                )
        else:
            lines.extend(["No adversarial review generated yet.", ""])

        lines.extend(["## Recommendation Memo", ""])
        if dossier.recommendation_memo:
            recommended_option = option_map.get(dossier.recommendation_memo.recommended_option_id)
            fallback_option = (
                option_map.get(dossier.recommendation_memo.fallback_option_id)
                if dossier.recommendation_memo.fallback_option_id
                else None
            )
            lines.extend(
                [
                    f"**Recommended Option:** {recommended_option.name if recommended_option else dossier.recommendation_memo.recommended_option_id}",
                    "",
                    f"**Confidence:** `{dossier.recommendation_memo.confidence.value}`",
                    "",
                    dossier.recommendation_memo.rationale,
                    "",
                ]
            )
            if fallback_option is not None:
                lines.extend(
                    [
                        f"**Fallback Option:** {fallback_option.name}",
                        "",
                    ]
                )
            lines.extend(["### Conditions", ""])
            for condition in dossier.recommendation_memo.conditions:
                lines.append(f"- {condition.statement}")
            lines.append("")
        else:
            lines.extend(["No recommendation memo generated yet.", ""])

        lines.extend(["## Traceability Notes", ""])
        lines.extend(
            [
                f"- Options recorded: `{len(dossier.options)}`",
                f"- Criteria recorded: `{len(dossier.criteria)}`",
                f"- Assumptions recorded: `{len(dossier.assumptions)}`",
                f"- Evidence recorded: `{len(dossier.evidence)}`",
                f"- Tradeoff matrix present: `{'yes' if dossier.tradeoff_matrix else 'no'}`",
                f"- Adversarial review present: `{'yes' if dossier.adversarial_review else 'no'}`",
                f"- Recommendation memo present: `{'yes' if dossier.recommendation_memo else 'no'}`",
                "",
            ]
        )

        return "\n".join(lines)
