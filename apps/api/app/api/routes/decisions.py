from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db_session
from app.domain.assumption import (
    Assumption,
    AssumptionCreate,
    AssumptionUpdate,
    build_bootstrap_assumptions,
)
from app.domain.criterion import (
    Criterion,
    CriterionCreate,
    CriterionUpdate,
    build_bootstrap_criteria,
)
from app.domain.decision import Decision, DecisionCreate, DecisionUpdate, build_bootstrap_decision
from app.domain.option import Option, OptionCreate, OptionUpdate, build_bootstrap_options
from app.domain.tradeoff_matrix import TradeoffMatrix
from app.persistence.assumption_repository import AssumptionRepository
from app.persistence.criterion_repository import CriterionRepository
from app.persistence.decision_repository import DecisionRepository
from app.persistence.option_repository import OptionRepository
from app.persistence.tradeoff_matrix_repository import TradeoffMatrixRepository
from app.services.assumption_generation import (
    AssumptionGenerationRequest,
    AssumptionGenerationResponse,
    AssumptionGenerationService,
)
from app.services.litellm_client import LiteLLMError
from app.services.tradeoff_matrix_generation import (
    TradeoffMatrixGenerationRequest,
    TradeoffMatrixGenerationResponse,
    TradeoffMatrixGenerationService,
)

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


@router.delete("/{decision_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_decision(
    decision_id: str,
    session: Session = Depends(get_db_session),
) -> None:
    repository = DecisionRepository(session)
    deleted = repository.delete(decision_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision '{decision_id}' was not found.",
        )


@router.post("/seed/bootstrap-example", response_model=Decision)
def seed_bootstrap_example(session: Session = Depends(get_db_session)) -> Decision:
    assumption_repository = AssumptionRepository(session)
    criterion_repository = CriterionRepository(session)
    decision_repository = DecisionRepository(session)
    option_repository = OptionRepository(session)

    decision = decision_repository.create_if_missing(build_bootstrap_decision())
    for option in build_bootstrap_options(decision.id):
        option_repository.create_if_missing(option)
    for criterion in build_bootstrap_criteria(decision.id):
        criterion_repository.create_if_missing(criterion)
    for assumption in build_bootstrap_assumptions(decision.id):
        assumption_repository.create_if_missing(assumption)
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


@router.get("/{decision_id}/assumptions", response_model=list[Assumption])
def list_decision_assumptions(
    decision_id: str,
    session: Session = Depends(get_db_session),
) -> list[Assumption]:
    require_decision(session, decision_id)
    repository = AssumptionRepository(session)
    return repository.list_for_decision(decision_id)


@router.post(
    "/{decision_id}/assumptions",
    response_model=Assumption,
    status_code=status.HTTP_201_CREATED,
)
def create_decision_assumption(
    decision_id: str,
    payload: AssumptionCreate,
    session: Session = Depends(get_db_session),
) -> Assumption:
    require_decision(session, decision_id)
    repository = AssumptionRepository(session)
    return repository.create(decision_id, payload)


@router.get("/{decision_id}/tradeoff-matrix", response_model=TradeoffMatrix)
def get_decision_tradeoff_matrix(
    decision_id: str,
    session: Session = Depends(get_db_session),
) -> TradeoffMatrix:
    require_decision(session, decision_id)
    repository = TradeoffMatrixRepository(session)
    matrix = repository.get_for_decision(decision_id)
    if matrix is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tradeoff matrix was not found for decision '{decision_id}'.",
        )
    return matrix


@router.post(
    "/{decision_id}/tradeoff-matrix/generate",
    response_model=TradeoffMatrixGenerationResponse,
)
def generate_decision_tradeoff_matrix(
    decision_id: str,
    payload: TradeoffMatrixGenerationRequest,
    session: Session = Depends(get_db_session),
) -> TradeoffMatrixGenerationResponse:
    require_decision(session, decision_id)
    service = TradeoffMatrixGenerationService(session)
    try:
        return service.generate_for_decision(decision_id, payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except LiteLLMError as error:
        detail = str(error)
        if error.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            detail = (
                "The configured AI provider is rate-limiting this workspace right now. "
                "Retry later or check the Gemini quota behind LiteLLM."
            )
        raise HTTPException(
            status_code=error.status_code,
            detail=detail,
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Tradeoff matrix generation failed: {error}",
        ) from error


@router.post(
    "/{decision_id}/assumptions/generate",
    response_model=AssumptionGenerationResponse,
)
def generate_decision_assumptions(
    decision_id: str,
    payload: AssumptionGenerationRequest,
    session: Session = Depends(get_db_session),
) -> AssumptionGenerationResponse:
    require_decision(session, decision_id)
    service = AssumptionGenerationService(session)
    try:
        return service.generate_for_decision(decision_id, payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except LiteLLMError as error:
        detail = str(error)
        if error.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            detail = (
                "The configured AI provider is rate-limiting this workspace right now. "
                "Retry later or check the Gemini quota behind LiteLLM."
            )
        raise HTTPException(
            status_code=error.status_code,
            detail=detail,
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Assumption generation failed: {error}",
        ) from error


@router.get("/{decision_id}/assumptions/{assumption_id}", response_model=Assumption)
def get_decision_assumption(
    decision_id: str,
    assumption_id: str,
    session: Session = Depends(get_db_session),
) -> Assumption:
    require_decision(session, decision_id)
    repository = AssumptionRepository(session)
    assumption = repository.get_for_decision(decision_id, assumption_id)
    if assumption is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assumption '{assumption_id}' was not found for decision '{decision_id}'.",
        )
    return assumption


@router.patch("/{decision_id}/assumptions/{assumption_id}", response_model=Assumption)
def update_decision_assumption(
    decision_id: str,
    assumption_id: str,
    payload: AssumptionUpdate,
    session: Session = Depends(get_db_session),
) -> Assumption:
    require_decision(session, decision_id)
    repository = AssumptionRepository(session)
    assumption = repository.update(decision_id, assumption_id, payload)
    if assumption is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assumption '{assumption_id}' was not found for decision '{decision_id}'.",
        )
    return assumption


@router.delete(
    "/{decision_id}/assumptions/{assumption_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_decision_assumption(
    decision_id: str,
    assumption_id: str,
    session: Session = Depends(get_db_session),
) -> None:
    require_decision(session, decision_id)
    repository = AssumptionRepository(session)
    deleted = repository.delete(decision_id, assumption_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assumption '{assumption_id}' was not found for decision '{decision_id}'.",
        )
