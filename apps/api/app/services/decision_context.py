from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.assumption import Assumption
from app.domain.criterion import Criterion
from app.domain.decision import Decision, DecisionType
from app.domain.evidence import Evidence
from app.domain.option import Option


class CompactDecisionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    decision_type: DecisionType
    known_facts: list[str] = Field(default_factory=list)
    options: list[str] = Field(default_factory=list)
    criteria: list[str] = Field(default_factory=list)
    critical_assumptions: list[str] = Field(default_factory=list)
    evidence_summary: list[str] = Field(default_factory=list)


def build_compact_decision_context(
    *,
    decision: Decision,
    options: list[Option],
    criteria: list[Criterion],
    assumptions: list[Assumption],
    evidence: list[Evidence],
) -> CompactDecisionContext:
    decision_type = classify_decision_type(decision=decision, options=options)
    known_facts = _extract_known_facts(decision=decision, evidence=evidence)
    evidence_summary = [
        _truncate_text(f"{item.title}: {item.summary}", limit=140) for item in evidence[:4]
    ]
    return CompactDecisionContext(
        question=_truncate_text(decision.question, limit=180),
        decision_type=decision_type,
        known_facts=known_facts[:5],
        options=[_truncate_text(option.name, limit=90) for option in options[:6]],
        criteria=[
            _truncate_text(
                f"{criterion.name} ({criterion.measurement_type.value}, weight {criterion.weight:.2f})",
                limit=90,
            )
            for criterion in criteria[:7]
        ],
        critical_assumptions=[
            _truncate_text(
                f"{assumption.statement} [{assumption.confidence.value}]",
                limit=110,
            )
            for assumption in assumptions[:5]
        ],
        evidence_summary=evidence_summary,
    )


def classify_decision_type(
    *,
    decision: Decision,
    options: list[Option],
) -> DecisionType:
    text = " ".join(
        value.lower()
        for value in [
            decision.title,
            decision.decision_brief,
            decision.question,
            decision.context,
        ]
        if value
    )
    question = decision.question.strip().lower()
    option_names = [option.name.strip().lower() for option in options]

    if any(keyword in text for keyword in ("design review", "architecture review", "ui review")):
        return DecisionType.DESIGN_REVIEW

    if _looks_like_factual_question(question=question, option_names=option_names):
        return DecisionType.FACTUAL_VERIFICATION

    if any(
        keyword in text
        for keyword in ("should we", "adopt", "invest", "roadmap", "strategy", "market")
    ):
        return DecisionType.STRATEGIC_DECISION

    if any(keyword in text for keyword in ("review", "architecture", "design")):
        return DecisionType.DESIGN_REVIEW

    return DecisionType.TRADEOFF_COMPARISON


def _looks_like_factual_question(*, question: str, option_names: list[str]) -> bool:
    factual_starters = ("is ", "are ", "can ", "does ", "do ", "will ", "whether ")
    factual = question.startswith(factual_starters)
    if not factual:
        return False
    if len(option_names) != 2:
        return True

    opposing_markers = [
        (" can ", " cannot "),
        ("supported", "not supported"),
        ("possible", "impossible"),
        ("feasible", "infeasible"),
        ("yes", "no"),
    ]
    joined = " | ".join(option_names)
    return any(left in joined and right in joined for left, right in opposing_markers)


def _extract_known_facts(*, decision: Decision, evidence: list[Evidence]) -> list[str]:
    facts: list[str] = []
    for value in [decision.decision_brief, decision.context]:
        facts.extend(_split_sentences(_truncate_text(value, limit=360)))
    for item in evidence[:3]:
        facts.append(_truncate_text(item.summary, limit=120))
    deduplicated: list[str] = []
    seen: set[str] = set()
    for fact in facts:
        normalized = " ".join(fact.split()).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(normalized)
    return deduplicated


def _split_sentences(value: str) -> list[str]:
    candidates = [segment.strip() for segment in value.replace("?", ".").split(".")]
    return [candidate for candidate in candidates if candidate][:4]


def _truncate_text(value: str, *, limit: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."
