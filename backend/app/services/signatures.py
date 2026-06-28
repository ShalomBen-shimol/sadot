"""Signature request lifecycle.

Signature requests are created by the adoption workflow via the signature
adapter (Mock in phase 1). This service simulates the provider's signing
callback/webhook: marking a request signed and, when that completes a related
adoption case, advancing its state machine.
"""
from sqlmodel import Session, select

from app.models.adoption import AdoptionCase
from app.models.base import utcnow
from app.models.enums import EntityType, SignatureStatus
from app.models.support import SignatureRequest
from app.services import adoption as adoption_service
from app.services import audit


def list_for_entity(
    session: Session,
    entity_type: EntityType | None = None,
    entity_id: int | None = None,
) -> list[SignatureRequest]:
    """List signature requests, optionally filtered to a single entity."""
    stmt = select(SignatureRequest)
    if entity_type is not None:
        stmt = stmt.where(SignatureRequest.related_entity_type == entity_type)
    if entity_id is not None:
        stmt = stmt.where(SignatureRequest.related_entity_id == entity_id)
    return list(session.exec(stmt).all())


def mark_signed(
    session: Session,
    sig: SignatureRequest,
    actor_user_id: int | None = None,
) -> SignatureRequest:
    """Simulate the provider callback for a signed document.

    Sets status=signed and signed_at, writes an audit entry, then nudges the
    related adoption case's state machine. Idempotent: re-marking an already
    signed request only re-evaluates the case advancement.
    """
    if sig.status != SignatureStatus.signed:
        sig.status = SignatureStatus.signed
        sig.signed_at = utcnow()
        session.add(sig)
        session.commit()
        session.refresh(sig)
        audit.log(
            session,
            action="signature_request.signed",
            actor_user_id=actor_user_id,
            entity_type="signature_request",
            entity_id=sig.id,
            metadata={
                "related_entity_type": sig.related_entity_type.value,
                "related_entity_id": sig.related_entity_id,
            },
        )

    if sig.related_entity_type == EntityType.adoption_case:
        case = session.get(AdoptionCase, sig.related_entity_id)
        if case:
            adoption_service.advance_after_signatures(
                session, case, actor_user_id=actor_user_id
            )

    return sig
