from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db_session
from app.domain.decision import Decision, DecisionCreate, DecisionUpdate, build_bootstrap_decision
from app.persistence.decision_repository import DecisionRepository

router = APIRouter()


@router.get("", response_model=list[Decision])
def list_decisions(session: Session = Depends(get_db_session)) -> list[Decision]:
    repository = DecisionRepository(session)
    return repository.list()


@router.post("", response_model=Decision, status_code=status.HTTP_201_CREATED)
def create_decision(
    payload: DecisionCreate,
    session: Session = Depends(get_db_session),
) -> Decision:
    repository = DecisionRepository(session)
    return repository.create(payload)


@router.get("/{decision_id}", response_model=Decision)
def get_decision(
    decision_id: str,
    session: Session = Depends(get_db_session),
) -> Decision:
    repository = DecisionRepository(session)
    decision = repository.get(decision_id)
    if decision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision '{decision_id}' was not found.",
        )
    return decision


@router.patch("/{decision_id}", response_model=Decision)
def update_decision(
    decision_id: str,
    payload: DecisionUpdate,
    session: Session = Depends(get_db_session),
) -> Decision:
    repository = DecisionRepository(session)
    decision = repository.update(decision_id, payload)
    if decision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision '{decision_id}' was not found.",
        )
    return decision


@router.post("/seed/bootstrap-example", response_model=Decision)
def seed_bootstrap_example(session: Session = Depends(get_db_session)) -> Decision:
    repository = DecisionRepository(session)
    return repository.create_if_missing(build_bootstrap_decision())
