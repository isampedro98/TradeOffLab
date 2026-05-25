from datetime import UTC, datetime

from fastapi import APIRouter

from app.domain.decision import Decision, DecisionStatus, DecisionType

router = APIRouter()


@router.get("/bootstrap-example")
def get_bootstrap_example() -> Decision:
    return Decision(
        id="decision-erp-bootstrap",
        title="ERPNext vs Tango vs Bejerman",
        question="Should we adopt ERPNext instead of Tango or Bejerman?",
        context=(
            "Bootstrap example for the TradeOffLab MVP. "
            "The goal is to model a local-first, structured decision workflow."
        ),
        type=DecisionType.ERP_ADOPTION,
        status=DecisionStatus.DRAFT,
        created_at=datetime.now(UTC),
    )

