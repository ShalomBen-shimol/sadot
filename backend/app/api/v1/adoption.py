from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, SessionDep
from app.models.adoption import AdoptionCase, AdoptionLead
from app.models.enums import AdoptionStatus
from app.repositories.base import CRUDRepository
from app.schemas.common import StatusTransition
from app.schemas.entities import AdoptionCaseCreate, AdoptionLeadCreate
from app.services import adoption as adoption_service

router = APIRouter(tags=["adoption"])
lead_repo = CRUDRepository(AdoptionLead)
case_repo = CRUDRepository(AdoptionCase)


# ---- Adoption leads ----
@router.get("/adoption-leads", response_model=list[AdoptionLead])
def list_leads(session: SessionDep, _: CurrentUser, offset: int = 0, limit: int = Query(100, le=500)):
    return lead_repo.list(session, offset=offset, limit=limit)


@router.post("/adoption-leads", response_model=AdoptionLead, status_code=status.HTTP_201_CREATED)
def create_lead(payload: AdoptionLeadCreate, session: SessionDep, _: CurrentUser):
    return adoption_service.create_lead(session, payload.model_dump(exclude_unset=True))


# ---- Adoption cases ----
@router.get("/adoption-cases", response_model=list[AdoptionCase])
def list_cases(
    session: SessionDep,
    _: CurrentUser,
    status_filter: AdoptionStatus | None = Query(default=None, alias="status"),
    offset: int = 0,
    limit: int = Query(100, le=500),
):
    filters = {"status": status_filter} if status_filter else None
    return case_repo.list(session, offset=offset, limit=limit, filters=filters)


@router.get("/adoption-cases/{case_id}", response_model=AdoptionCase)
def get_case(case_id: int, session: SessionDep, _: CurrentUser):
    case = case_repo.get(session, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Adoption case not found")
    return case


@router.post("/adoption-cases", response_model=AdoptionCase, status_code=status.HTTP_201_CREATED)
def create_case(payload: AdoptionCaseCreate, session: SessionDep, _: CurrentUser):
    return adoption_service.create_case(session, payload.model_dump(exclude_unset=True))


@router.post("/adoption-cases/{case_id}/status", response_model=AdoptionCase)
def set_status(case_id: int, payload: StatusTransition, session: SessionDep, _: CurrentUser):
    case = case_repo.get(session, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Adoption case not found")
    try:
        case.status = AdoptionStatus(payload.status)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid status")
    return case_repo.save(session, case)


@router.post("/adoption-cases/{case_id}/approve", response_model=AdoptionCase)
def approve(case_id: int, session: SessionDep, user: CurrentUser):
    case = case_repo.get(session, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Adoption case not found")
    return adoption_service.approve(session, case, actor_user_id=user.id)


@router.post("/adoption-cases/{case_id}/complete", response_model=AdoptionCase)
def complete(case_id: int, session: SessionDep, user: CurrentUser):
    case = case_repo.get(session, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Adoption case not found")
    return adoption_service.complete(session, case, actor_user_id=user.id)
