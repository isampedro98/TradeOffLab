from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.db import get_db_session
from app.domain.adversarial_review import AdversarialReview
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
from app.domain.evidence import Evidence, EvidenceCreate, EvidenceUpdate, build_bootstrap_evidence
from app.domain.option import Option, OptionCreate, OptionUpdate, build_bootstrap_options
from app.domain.recommendation_memo import RecommendationMemo
from app.domain.tradeoff_matrix import TradeoffMatrix
from app.persistence.assumption_repository import AssumptionRepository
from app.persistence.adversarial_review_repository import AdversarialReviewRepository
from app.persistence.criterion_repository import CriterionRepository
from app.persistence.decision_repository import DecisionRepository
from app.persistence.evidence_repository import EvidenceRepository
from app.persistence.option_repository import OptionRepository
from app.persistence.recommendation_memo_repository import RecommendationMemoRepository
from app.persistence.tradeoff_matrix_repository import TradeoffMatrixRepository
from app.services.assumption_generation import (
    AssumptionGenerationRequest,
    AssumptionGenerationResponse,
    AssumptionGenerationService,
)
from app.services.adversarial_review_generation import (
    AdversarialReviewGenerationRequest,
    AdversarialReviewGenerationResponse,
    AdversarialReviewGenerationService,
)
from app.services.criteria_generation import (
    CriteriaGenerationRequest,
    CriteriaGenerationResponse,
    CriteriaGenerationService,
)
from app.services.evidence_generation import (
    EvidenceGenerationRequest,
    EvidenceGenerationResponse,
    EvidenceGenerationService,
)
from app.services.litellm_client import LiteLLMError
from app.services.decision_export import DecisionDossierExport, DecisionExportService
from app.services.recommendation_memo_generation import (
    RecommendationMemoGenerationRequest,
    RecommendationMemoGenerationResponse,
    RecommendationMemoGenerationService,
)
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


@router.get("/{decision_id}/export/json", response_model=DecisionDossierExport)
def export_decision_json(
    decision_id: str,
    session: Session = Depends(get_db_session),
) -> DecisionDossierExport:
    service = DecisionExportService(session)
    try:
        return service.build_dossier(decision_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.get("/{decision_id}/export/markdown", response_class=PlainTextResponse)
def export_decision_markdown(
    decision_id: str,
    session: Session = Depends(get_db_session),
) -> Response:
    service = DecisionExportService(session)
    try:
        markdown = service.build_markdown(decision_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    filename = f"{decision_id}.md"
    return PlainTextResponse(
        content=markdown,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


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
    evidence_repository = EvidenceRepository(session)
    option_repository = OptionRepository(session)

    decision = decision_repository.create_if_missing(build_bootstrap_decision())
    for option in build_bootstrap_options(decision.id):
        option_repository.create_if_missing(option)
    for criterion in build_bootstrap_criteria(decision.id):
        criterion_repository.create_if_missing(criterion)
    for assumption in build_bootstrap_assumptions(decision.id):
        assumption_repository.create_if_missing(assumption)
    for evidence in build_bootstrap_evidence(decision.id):
        evidence_repository.create_if_missing(evidence)
    return decision


@router.get("/{decision_id}/evidence", response_model=list[Evidence])
def list_decision_evidence(
    decision_id: str,
    session: Session = Depends(get_db_session),
) -> list[Evidence]:
    require_decision(session, decision_id)
    repository = EvidenceRepository(session)
    return repository.list_for_decision(decision_id)


@router.post(
    "/{decision_id}/evidence",
    response_model=Evidence,
    status_code=status.HTTP_201_CREATED,
)
def create_decision_evidence(
    decision_id: str,
    payload: EvidenceCreate,
    session: Session = Depends(get_db_session),
) -> Evidence:
    require_decision(session, decision_id)
    repository = EvidenceRepository(session)
    return repository.create(decision_id, payload)


@router.post(
    "/{decision_id}/evidence/generate",
    response_model=EvidenceGenerationResponse,
)
def generate_decision_evidence(
    decision_id: str,
    payload: EvidenceGenerationRequest,
    session: Session = Depends(get_db_session),
) -> EvidenceGenerationResponse:
    require_decision(session, decision_id)
    service = EvidenceGenerationService(session)
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
                "Retry later or check the upstream provider behind LiteLLM."
            )
        raise HTTPException(
            status_code=error.status_code,
            detail=detail,
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Evidence generation failed: {error}",
        ) from error


@router.get("/{decision_id}/evidence/{evidence_id}", response_model=Evidence)
def get_decision_evidence(
    decision_id: str,
    evidence_id: str,
    session: Session = Depends(get_db_session),
) -> Evidence:
    require_decision(session, decision_id)
    repository = EvidenceRepository(session)
    evidence = repository.get_for_decision(decision_id, evidence_id)
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence '{evidence_id}' was not found for decision '{decision_id}'.",
        )
    return evidence


@router.patch("/{decision_id}/evidence/{evidence_id}", response_model=Evidence)
def update_decision_evidence(
    decision_id: str,
    evidence_id: str,
    payload: EvidenceUpdate,
    session: Session = Depends(get_db_session),
) -> Evidence:
    require_decision(session, decision_id)
    repository = EvidenceRepository(session)
    evidence = repository.update(decision_id, evidence_id, payload)
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence '{evidence_id}' was not found for decision '{decision_id}'.",
        )
    return evidence


@router.delete("/{decision_id}/evidence/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_decision_evidence(
    decision_id: str,
    evidence_id: str,
    session: Session = Depends(get_db_session),
) -> None:
    require_decision(session, decision_id)
    repository = EvidenceRepository(session)
    deleted = repository.delete(decision_id, evidence_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence '{evidence_id}' was not found for decision '{decision_id}'.",
        )


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


@router.post(
    "/{decision_id}/criteria/generate",
    response_model=CriteriaGenerationResponse,
)
def generate_decision_criteria(
    decision_id: str,
    payload: CriteriaGenerationRequest,
    session: Session = Depends(get_db_session),
) -> CriteriaGenerationResponse:
    require_decision(session, decision_id)
    service = CriteriaGenerationService(session)
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
                "Retry later or check the upstream provider behind LiteLLM."
            )
        raise HTTPException(
            status_code=error.status_code,
            detail=detail,
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Criteria generation failed: {error}",
        ) from error


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
                "Retry later or check the upstream provider behind LiteLLM."
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


@router.get("/{decision_id}/adversarial-review", response_model=AdversarialReview)
def get_decision_adversarial_review(
    decision_id: str,
    session: Session = Depends(get_db_session),
) -> AdversarialReview:
    require_decision(session, decision_id)
    repository = AdversarialReviewRepository(session)
    review = repository.get_for_decision(decision_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adversarial review was not found for decision '{decision_id}'.",
        )
    return review


@router.get("/{decision_id}/recommendation-memo", response_model=RecommendationMemo)
def get_decision_recommendation_memo(
    decision_id: str,
    session: Session = Depends(get_db_session),
) -> RecommendationMemo:
    require_decision(session, decision_id)
    repository = RecommendationMemoRepository(session)
    memo = repository.get_for_decision(decision_id)
    if memo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation memo was not found for decision '{decision_id}'.",
        )
    return memo


@router.post(
    "/{decision_id}/adversarial-review/generate",
    response_model=AdversarialReviewGenerationResponse,
)
def generate_decision_adversarial_review(
    decision_id: str,
    payload: AdversarialReviewGenerationRequest,
    session: Session = Depends(get_db_session),
) -> AdversarialReviewGenerationResponse:
    require_decision(session, decision_id)
    service = AdversarialReviewGenerationService(session)
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
                "Retry later or check the upstream provider behind LiteLLM."
            )
        raise HTTPException(
            status_code=error.status_code,
            detail=detail,
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Adversarial review generation failed: {error}",
        ) from error


@router.post(
    "/{decision_id}/recommendation-memo/generate",
    response_model=RecommendationMemoGenerationResponse,
)
def generate_decision_recommendation_memo(
    decision_id: str,
    payload: RecommendationMemoGenerationRequest,
    session: Session = Depends(get_db_session),
) -> RecommendationMemoGenerationResponse:
    require_decision(session, decision_id)
    service = RecommendationMemoGenerationService(session)
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
                "Retry later or check the upstream provider behind LiteLLM."
            )
        raise HTTPException(
            status_code=error.status_code,
            detail=detail,
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Recommendation memo generation failed: {error}",
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
                "Retry later or check the upstream provider behind LiteLLM."
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
