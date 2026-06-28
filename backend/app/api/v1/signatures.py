"""Signature request endpoints: list per entity and mock the signing callback."""
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.models.enums import EntityType
from app.models.support import SignatureRequest
from app.repositories.base import CRUDRepository
from app.services import signatures as signatures_service

router = APIRouter(prefix="/signatures", tags=["signatures"])
sig_repo = CRUDRepository(SignatureRequest)


@router.get("", response_model=list[SignatureRequest])
def list_signatures(
    session: SessionDep,
    _: CurrentUser,
    entity_type: EntityType | None = None,
    entity_id: int | None = None,
):
    """List signature requests, optionally filtered by related entity."""
    return signatures_service.list_for_entity(session, entity_type, entity_id)


@router.get("/{signature_id}", response_model=SignatureRequest)
def get_signature(signature_id: int, session: SessionDep, _: CurrentUser):
    sig = sig_repo.get(session, signature_id)
    if not sig:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signature request not found")
    return sig


@router.post("/{signature_id}/mark-signed", response_model=SignatureRequest)
def mark_signed(signature_id: int, session: SessionDep, user: CurrentUser):
    """Simulate the signature provider's callback marking the document signed."""
    sig = sig_repo.get(session, signature_id)
    if not sig:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signature request not found")
    return signatures_service.mark_signed(session, sig, actor_user_id=user.id)
