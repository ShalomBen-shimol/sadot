from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, SessionDep
from app.models.ownership import OwnershipTransfer
from app.models.support import Document
from app.repositories.base import CRUDRepository
from app.schemas.entities import OwnershipTransferCreate
from app.services import forms as forms_service
from app.services import ownership as ownership_service
from app.services import workflow as workflow_service

router = APIRouter(prefix="/ownership-transfers", tags=["ownership"])
repo = CRUDRepository(OwnershipTransfer)


@router.get("/{transfer_id}/workflow")
def get_transfer_workflow(transfer_id: int, session: SessionDep, _: CurrentUser):
    t = repo.get(session, transfer_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return workflow_service.status(session, t)


@router.post("/{transfer_id}/advance")
def advance_transfer_workflow(
    transfer_id: int, session: SessionDep, _: CurrentUser, run_action: bool = False
):
    """Advance the configurable workflow: pass any newly-satisfied gates, and if
    `run_action` fire the current manual action (e.g. send to authority)."""
    t = repo.get(session, transfer_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return workflow_service.advance(session, t, run_current_action=run_action)


@router.post(
    "/{transfer_id}/generate-form", response_model=Document, status_code=status.HTTP_201_CREATED
)
def generate_transfer_form(transfer_id: int, session: SessionDep, user: CurrentUser):
    """Produce the ownership-transfer form (PDF) + open the signature request and
    a follow-up task. The required-documents checklist also asks for the new
    owner's photo with the dog (for individual-to-individual transfers)."""
    t = repo.get(session, transfer_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return forms_service.generate_transfer_form(session, t, actor_user_id=user.id)


@router.get("", response_model=list[OwnershipTransfer])
def list_transfers(session: SessionDep, _: CurrentUser, offset: int = 0, limit: int = Query(100, le=500)):
    return repo.list(session, offset=offset, limit=limit)


@router.get("/{transfer_id}", response_model=OwnershipTransfer)
def get_transfer(transfer_id: int, session: SessionDep, _: CurrentUser):
    t = repo.get(session, transfer_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return t


@router.post("", response_model=OwnershipTransfer, status_code=status.HTTP_201_CREATED)
def create_transfer(payload: OwnershipTransferCreate, session: SessionDep, _: CurrentUser):
    return ownership_service.create_transfer(session, payload.model_dump(exclude_unset=True))


@router.get("/{transfer_id}/required-documents")
def required_documents(transfer_id: int, session: SessionDep, _: CurrentUser):
    t = repo.get(session, transfer_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return {
        "required": [d.value for d in ownership_service.required_documents(t)],
        "complete": ownership_service.has_all_documents(session, t),
    }


@router.post("/{transfer_id}/send-to-authority", response_model=OwnershipTransfer)
def send_to_authority(transfer_id: int, session: SessionDep, user: CurrentUser):
    t = repo.get(session, transfer_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return ownership_service.send_to_authority(session, t, actor_user_id=user.id)


@router.post("/{transfer_id}/confirm", response_model=OwnershipTransfer)
def confirm(transfer_id: int, session: SessionDep, user: CurrentUser):
    t = repo.get(session, transfer_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return ownership_service.confirm(session, t, actor_user_id=user.id)


@router.post("/{transfer_id}/stop", response_model=OwnershipTransfer)
def stop(transfer_id: int, session: SessionDep, user: CurrentUser):
    t = repo.get(session, transfer_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return ownership_service.stop_manually(session, t, actor_user_id=user.id)


@router.post("/run-followups")
def run_followups(session: SessionDep, _: CurrentUser):
    """Manually trigger the due follow-up sweep (also run by the scheduler)."""
    count = ownership_service.run_due_followups(session)
    return {"detail": "Follow-up sweep complete", "reminders_created": count}
