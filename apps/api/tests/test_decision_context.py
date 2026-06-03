from app.domain.decision import DecisionType, build_bootstrap_decision
from app.domain.evidence import build_bootstrap_evidence
from app.domain.option import build_bootstrap_options
from app.domain.criterion import build_bootstrap_criteria
from app.domain.assumption import build_bootstrap_assumptions
from app.services.decision_context import build_compact_decision_context, classify_decision_type


def test_classify_decision_type_marks_factual_binary_question() -> None:
    decision = build_bootstrap_decision().model_copy(
        update={
            "title": "Hyper-V extendable HDD space",
            "decision_brief": "Verify whether a Hyper-V Ubuntu VM disk can be expanded.",
            "question": "Can a Hyper-V instance running Ubuntu extend its virtual disk space?",
            "context": "The current VM was created with 20GB and may need more capacity.",
        }
    )
    options = [
        option.model_copy(update={"name": name, "description": name})
        for option, name in zip(
            build_bootstrap_options(decision.id)[:2],
            [
                "Windows Hyper-V space can be extendable",
                "Windows Hyper-V space cannot be extendable",
            ],
            strict=True,
        )
    ]

    decision_type = classify_decision_type(decision=decision, options=options)

    assert decision_type == DecisionType.FACTUAL_VERIFICATION


def test_build_compact_decision_context_includes_expected_sections() -> None:
    decision = build_bootstrap_decision()
    context = build_compact_decision_context(
        decision=decision,
        options=build_bootstrap_options(decision.id),
        criteria=build_bootstrap_criteria(decision.id),
        assumptions=build_bootstrap_assumptions(decision.id),
        evidence=build_bootstrap_evidence(decision.id),
    )

    assert context.question
    assert context.decision_type == DecisionType.STRATEGIC_DECISION
    assert context.options
    assert context.criteria
    assert context.critical_assumptions
    assert context.evidence_summary
