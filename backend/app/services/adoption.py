"""Adoption workflow: lead -> case -> approval -> ownership transfer -> done."""
from sqlmodel import Session, select

from app.adapters import get_signature_provider
from app.models.adoption import AdoptionCase, AdoptionLead
from app.models.dog import Dog
from app.models.enums import (
    AdoptionStatus,
    DogStatus,
    EntityType,
    SignatureStatus,
    SignatureType,
    TransferType,
)
from app.models.person import Person
from app.models.support import SignatureRequest
from app.services import audit
from app.services import ownership as ownership_service
from app.services.notifications import send_whatsapp


def create_lead(session: Session, data: dict) -> AdoptionLead:
    lead = AdoptionLead(**data)
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


def create_case(session: Session, data: dict) -> AdoptionCase:
    case = AdoptionCase(**data)
    session.add(case)
    session.commit()
    session.refresh(case)
    # Reserve the dog while the case is active.
    dog = session.get(Dog, case.dog_id)
    if dog and dog.status == DogStatus.available_for_adoption:
        dog.status = DogStatus.reserved
        session.add(dog)
        session.commit()
    # The commit above expires `case`; refresh so the response is fully populated.
    session.refresh(case)
    return case


def _create_signature(session: Session, case: AdoptionCase, person_id: int, sig_type: SignatureType) -> SignatureRequest:
    provider = get_signature_provider()
    person = session.get(Person, person_id)
    signer_name = person.first_name if person else "signer"
    sess = provider.create_request(signer_name, f"Adoption case #{case.id}")
    req = SignatureRequest(
        related_entity_type=EntityType.adoption_case,
        related_entity_id=case.id,
        signer_person_id=person_id,
        signature_type=sig_type,
        status=SignatureStatus.sent,
        sign_url=sess.sign_url,
        provider_reference=sess.provider_reference,
    )
    session.add(req)
    session.commit()
    session.refresh(req)
    return req


def approve(session: Session, case: AdoptionCase, actor_user_id: int | None = None) -> AdoptionCase:
    """Open the ownership transfer and dispatch signature requests."""
    dog = session.get(Dog, case.dog_id)

    # Determine transfer type and the 'from' party.
    if case.is_direct_home_adoption:
        transfer_type = TransferType.direct_surrenderer_to_adopter
        from_person_id = dog.current_owner_person_id if dog else None
    else:
        transfer_type = TransferType.facility_to_adopter
        from_person_id = dog.current_owner_person_id if dog else None

    from_person = session.get(Person, from_person_id) if from_person_id else None
    adopter = session.get(Person, case.adopter_person_id)

    transfer = ownership_service.create_transfer(
        session,
        {
            "dog_id": case.dog_id,
            "from_person_id": from_person_id,
            "to_person_id": case.adopter_person_id,
            "transfer_type": transfer_type,
        },
        from_city=from_person.city if from_person else None,
        to_city=adopter.city if adopter else None,
    )

    # Signature requests: receiver/adopter always; surrenderer for direct adoptions.
    _create_signature(session, case, case.adopter_person_id, SignatureType.adopter)
    if from_person_id:
        _create_signature(session, case, from_person_id, SignatureType.surrenderer)

    case.status = AdoptionStatus.waiting_for_signatures
    session.add(case)
    session.commit()
    session.refresh(case)
    audit.log(
        session,
        action="adoption_case.approved",
        actor_user_id=actor_user_id,
        entity_type="adoption_case",
        entity_id=case.id,
        metadata={"ownership_transfer_id": transfer.id},
    )
    return case


def advance_after_signatures(
    session: Session, case: AdoptionCase, actor_user_id: int | None = None
) -> AdoptionCase:
    """State machine: once every signature request for the case is signed,
    move the case from waiting_for_signatures to waiting_for_documents.

    Idempotent and a no-op while signatures are outstanding or the case is in
    any other state.
    """
    if case.status != AdoptionStatus.waiting_for_signatures:
        return case

    sigs = session.exec(
        select(SignatureRequest).where(
            SignatureRequest.related_entity_type == EntityType.adoption_case,
            SignatureRequest.related_entity_id == case.id,
        )
    ).all()
    if not sigs or not all(s.status == SignatureStatus.signed for s in sigs):
        return case

    case.status = AdoptionStatus.waiting_for_documents
    session.add(case)
    session.commit()
    session.refresh(case)
    audit.log(
        session,
        action="adoption_case.signatures_completed",
        actor_user_id=actor_user_id,
        entity_type="adoption_case",
        entity_id=case.id,
        metadata={"signature_count": len(sigs)},
    )
    return case


def complete(session: Session, case: AdoptionCase, actor_user_id: int | None = None) -> AdoptionCase:
    """Mark the adoption complete: dog adopted, request a home video, offer shop."""
    case.status = AdoptionStatus.completed
    session.add(case)
    session.commit()

    dog = session.get(Dog, case.dog_id)
    if dog:
        dog.status = DogStatus.adopted
        dog.current_owner_person_id = case.adopter_person_id
        session.add(dog)
        session.commit()

    adopter = session.get(Person, case.adopter_person_id)
    if adopter:
        send_whatsapp(
            session,
            adopter,
            "מזל טוב על האימוץ! נשמח לקבל תמונה או סרטון קצר של הכלב בבית החדש 🐾",
            intent="post_adoption_media_request",
        )
        send_whatsapp(
            session,
            adopter,
            "כברכת הצטרפות הכנו לכם הטבות בחנות לאוכל ואביזרים. נשלח קוד קופון בהמשך.",
            intent="shop_offer",
        )

    audit.log(
        session,
        action="adoption_case.completed",
        actor_user_id=actor_user_id,
        entity_type="adoption_case",
        entity_id=case.id,
    )
    session.refresh(case)
    return case
