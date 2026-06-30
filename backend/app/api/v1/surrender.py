from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, SessionDep
from app.models.enums import SurrenderStatus, SurrenderType
from app.models.surrender import SubscriptionPayment, SurrenderCase
from app.models.support import Document
from app.repositories.base import CRUDRepository
from app.schemas.entities import SurrenderCreate, SurrenderUpdate
from app.services import forms as forms_service
from app.services import surrender as surrender_service

router = APIRouter(prefix="/surrender-cases", tags=["surrender"])
repo = CRUDRepository(SurrenderCase)


def _get_case_or_404(case_id: int, session: SessionDep) -> SurrenderCase:
    case = repo.get(session, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surrender case not found")
    return case


@router.post("/{case_id}/generate-form", response_model=Document, status_code=status.HTTP_201_CREATED)
def generate_surrender_form(case_id: int, session: SessionDep, user: CurrentUser):
    """Produce the signed forfeit form (PDF) + open the signature request and a
    follow-up task to collect the signed form and the owner's ID photo."""
    case = _get_case_or_404(case_id, session)
    return forms_service.generate_surrender_form(session, case, actor_user_id=user.id)


@router.get("", response_model=list[SurrenderCase])
def list_cases(
    session: SessionDep,
    _: CurrentUser,
    status_filter: SurrenderStatus | None = Query(default=None, alias="status"),
    offset: int = 0,
    limit: int = Query(100, le=500),
):
    filters = {"status": status_filter} if status_filter else None
    return repo.list(session, offset=offset, limit=limit, filters=filters)


@router.get("/{case_id}", response_model=SurrenderCase)
def get_case(case_id: int, session: SessionDep, _: CurrentUser):
    case = repo.get(session, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Surrender case not found")
    return case


@router.post("", response_model=SurrenderCase, status_code=status.HTTP_201_CREATED)
def create_case(payload: SurrenderCreate, session: SessionDep, _: CurrentUser):
    return surrender_service.create_case(session, payload.model_dump(exclude_unset=True))


@router.patch("/{case_id}", response_model=SurrenderCase)
def update_case(case_id: int, payload: SurrenderUpdate, session: SessionDep, _: CurrentUser):
    case = repo.get(session, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Surrender case not found")
    return repo.update(session, case, payload.model_dump(exclude_unset=True))


@router.post("/{case_id}/activate-home-subscription", response_model=SurrenderCase)
def activate_home_subscription(case_id: int, session: SessionDep, _: CurrentUser):
    case = repo.get(session, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Surrender case not found")
    if case.surrender_type != SurrenderType.home_subscription:
        raise HTTPException(status_code=422, detail="Case is not a home subscription")
    return surrender_service.activate_home_subscription(session, case)


@router.post("/{case_id}/charge-month", response_model=SubscriptionPayment)
def charge_month(case_id: int, session: SessionDep, _: CurrentUser):
    case = repo.get(session, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Surrender case not found")
    month = surrender_service._next_month_index(session, case)
    return surrender_service.record_subscription_payment(session, case, month)


@router.get("/{case_id}/payments", response_model=list[SubscriptionPayment])
def list_payments(case_id: int, session: SessionDep, _: CurrentUser):
    return CRUDRepository(SubscriptionPayment).list(session, filters={"surrender_case_id": case_id})


@router.post("/{case_id}/start-facility-transfer")
def start_facility_transfer(case_id: int, session: SessionDep, _: CurrentUser):
    case = repo.get(session, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Surrender case not found")
    transfer = surrender_service.start_facility_transfer(session, case)
    return {"detail": "Ownership transfer opened", "ownership_transfer_id": transfer.id}


@router.post("/{case_id}/convert-to-facility")
def convert_to_facility(case_id: int, session: SessionDep, _: CurrentUser):
    """Convert an accrued home subscription into a facility surrender (~7 months)."""
    case = repo.get(session, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Surrender case not found")
    transfer = surrender_service.convert_home_to_facility(session, case)
    return {
        "detail": "Converted to facility surrender",
        "accumulated_credit": case.accumulated_credit,
        "ownership_transfer_id": transfer.id,
    }
