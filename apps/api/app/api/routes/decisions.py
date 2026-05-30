from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db_session
from app.domain.criterion import (
    Criterion,
    CriterionCreate,
    CriterionUpdate,
    build_bootstrap_criteria,
)
from app.domain.decision import Decision, DecisionCreate, DecisionUpdate, build_bootstrap_decision
from app.domain.option import Option, OptionCreate, OptionUpdate, build_bootstrap_options
from app.persistence.criterion_repository import CriterionRepository
from app.persistence.decision_repository import DecisionRepository
from app.persistence.option_repository import OptionRepository

router = APIRouter()


def require_decision(session: Session, decision_id: str) -> Decision:
    repository = DecisionRepository(session)
    decision = repository.get(decision_id)
    if decision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision '{decision_id}' was not found.",
        )
    return decision


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
    return require_decision(session, decision_id)


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
    criterion_repository = CriterionRepository(session)
    decision_repository = DecisionRepository(session)
    option_repository = OptionRepository(session)

    decision = decision_repository.create_if_missing(build_bootstrap_decision())
    for option in build_bootstrap_options(decision.id):
        option_repository.create_if_missing(option)
    for criterion in build_bootstrap_criteria(decision.id):
        criterion_repository.create_if_missing(criterion)
    return decision


@router.get("/{decision_id}/options", response_model=list[Option])
def list_decision_options(
    decision_id: str,
    session: Session = Depends(get_db_session),
) -> list[Option]:
    require_decision(session, decision_id)
    repository = OptionRepository(session)
    return repository.list_for_decision(decision_id)


@router.post(
    "/{decision_id}/options",
    response_model=Option,
    status_code=status.HTTP_201_CREATED,
)
def create_decision_option(
    decision_id: str,
    payload: OptionCreate,
    session: Session = Depends(get_db_session),
) -> Option:
    require_decision(session, decision_id)
    repository = OptionRepository(session)
    return repository.create(decision_id, payload)


@router.get("/{decision_id}/options/{option_id}", response_model=Option)
def get_decision_option(
    decision_id: str,
    option_id: str,
    session: Session = Depends(get_db_session),
) -> Option:
    require_decision(session, decision_id)
    repository = OptionRepository(session)
    option = repository.get_for_decision(decision_id, option_id)
    if option is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option '{option_id}' was not found for decision '{decision_id}'.",
        )
    return option


@router.patch("/{decision_id}/options/{option_id}", response_model=Option)
def update_decision_option(
    decision_id: str,
    option_id: str,
    payload: OptionUpdate,
    session: Session = Depends(get_db_session),
) -> Option:
    require_decision(session, decision_id)
    repository = OptionRepository(session)
    option = repository.update(decision_id, option_id, payload)
    if option is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option '{option_id}' was not found for decision '{decision_id}'.",
        )
    return option


@router.delete("/{decision_id}/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_decision_option(
    decision_id: str,
    option_id: str,
    session: Session = Depends(get_db_session),
) -> None:
    require_decision(session, decision_id)
    repository = OptionRepository(session)
    deleted = repository.delete(decision_id, option_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option '{option_id}' was not found for decision '{decision_id}'.",
        )


@router.get("/{decision_id}/criteria", response_model=list[Criterion])
def list_decision_criteria(
    decision_id: str,
    session: Session = Depends(get_db_session),
) -> list[Criterion]:
    require_decision(session, decision_id)
    repository = CriterionRepository(session)
    return repository.list_for_decision(decision_id)


@router.post(
    "/{decision_id}/criteria",
    response_model=Criterion,
    status_code=status.HTTP_201_CREATED,
)
def create_decision_criterion(
    decision_id: str,
    payload: CriterionCreate,
    session: Session = Depends(get_db_session),
) -> Criterion:
    require_decision(session, decision_id)
    repository = CriterionRepository(session)
    return repository.create(decision_id, payload)


@router.get("/{decision_id}/criteria/{criterion_id}", response_model=Criterion)
def get_decision_criterion(
    decision_id: str,
    criterion_id: str,
    session: Session = Depends(get_db_session),
) -> Criterion:
    require_decision(session, decision_id)
    repository = CriterionRepository(session)
    criterion = repository.get_for_decision(decision_id, criterion_id)
    if criterion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Criterion '{criterion_id}' was not found for decision '{decision_id}'.",
        )
    return criterion


@router.patch("/{decision_id}/criteria/{criterion_id}", response_model=Criterion)
def update_decision_criterion(
    decision_id: str,
    criterion_id: str,
    payload: CriterionUpdate,
    session: Session = Depends(get_db_session),
) -> Criterion:
    require_decision(session, decision_id)
    repository = CriterionRepository(session)
    criterion = repository.update(decision_id, criterion_id, payload)
    if criterion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Criterion '{criterion_id}' was not found for decision '{decision_id}'.",
        )
    return criterion


@router.delete(
    "/{decision_id}/criteria/{criterion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_decision_criterion(
    decision_id: str,
    criterion_id: str,
    session: Session = Depends(get_db_session),
) -> None:
    require_decision(session, decision_id)
    repository = CriterionRepository(session)
    deleted = repository.delete(decision_id, criterion_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Criterion '{criterion_id}' was not found for decision '{decision_id}'.",
        )
