"""Back-office aggregation service.

Builds the read-only "case file" views the CRM screens need by gathering an
entity together with everything linked to it. Pure reads — no mutations, no
side effects beyond the queries themselves.
"""
from sqlmodel import Session, select

from app.models.adoption import AdoptionCase, AdoptionLead
from app.models.dog import Dog, DogPhoto
from app.models.enums import EntityType
from app.models.municipality import Municipality
from app.models.ownership import OwnershipTransfer
from app.models.person import Person
from app.models.support import Document, Message, SignatureRequest
from app.models.surrender import SurrenderCase
from app.schemas.backoffice import DogFile, OwnershipTransferDetail, PersonFile
from app.services import ownership as ownership_service

RECENT_MESSAGES_LIMIT = 20


def _documents_for(session: Session, entity_type: EntityType, entity_id: int) -> list[Document]:
    return list(
        session.exec(
            select(Document)
            .where(
                Document.related_entity_type == entity_type,
                Document.related_entity_id == entity_id,
            )
            .order_by(Document.created_at.desc())  # type: ignore[attr-defined]
        ).all()
    )


def build_person_file(session: Session, person: Person) -> PersonFile:
    dogs_owned = list(
        session.exec(select(Dog).where(Dog.current_owner_person_id == person.id)).all()
    )
    surrender_cases = list(
        session.exec(
            select(SurrenderCase).where(SurrenderCase.surrenderer_person_id == person.id)
        ).all()
    )
    adoption_cases = list(
        session.exec(
            select(AdoptionCase).where(AdoptionCase.adopter_person_id == person.id)
        ).all()
    )
    adoption_leads = list(
        session.exec(select(AdoptionLead).where(AdoptionLead.person_id == person.id)).all()
    )
    recent_messages = list(
        session.exec(
            select(Message)
            .where(Message.person_id == person.id)
            .order_by(Message.created_at.desc())  # type: ignore[attr-defined]
            .limit(RECENT_MESSAGES_LIMIT)
        ).all()
    )
    return PersonFile(
        person=person,
        dogs_owned=dogs_owned,
        surrender_cases=surrender_cases,
        adoption_cases=adoption_cases,
        adoption_leads=adoption_leads,
        documents=_documents_for(session, EntityType.person, person.id),
        recent_messages=recent_messages,
    )


def build_dog_file(session: Session, dog: Dog) -> DogFile:
    current_owner = (
        session.get(Person, dog.current_owner_person_id)
        if dog.current_owner_person_id
        else None
    )
    surrender_cases = list(
        session.exec(select(SurrenderCase).where(SurrenderCase.dog_id == dog.id)).all()
    )
    adoption_cases = list(
        session.exec(select(AdoptionCase).where(AdoptionCase.dog_id == dog.id)).all()
    )
    adoption_leads = list(
        session.exec(select(AdoptionLead).where(AdoptionLead.dog_id == dog.id)).all()
    )
    ownership_transfers = list(
        session.exec(
            select(OwnershipTransfer)
            .where(OwnershipTransfer.dog_id == dog.id)
            .order_by(OwnershipTransfer.created_at.desc())  # type: ignore[attr-defined]
        ).all()
    )
    photos = list(
        session.exec(select(DogPhoto).where(DogPhoto.dog_id == dog.id)).all()
    )
    return DogFile(
        dog=dog,
        current_owner=current_owner,
        surrender_cases=surrender_cases,
        adoption_cases=adoption_cases,
        adoption_leads=adoption_leads,
        ownership_transfers=ownership_transfers,
        documents=_documents_for(session, EntityType.dog, dog.id),
        photos=photos,
    )


def build_transfer_detail(
    session: Session, transfer: OwnershipTransfer
) -> OwnershipTransferDetail:
    def _authority_name(authority_id: int | None) -> str | None:
        if not authority_id:
            return None
        authority = session.get(Municipality, authority_id)
        if not authority:
            return None
        return authority.authority_name or authority.city_name

    signature_requests = list(
        session.exec(
            select(SignatureRequest).where(
                SignatureRequest.related_entity_type == EntityType.ownership_transfer,
                SignatureRequest.related_entity_id == transfer.id,
            )
        ).all()
    )
    return OwnershipTransferDetail(
        transfer=transfer,
        dog=session.get(Dog, transfer.dog_id) if transfer.dog_id else None,
        from_person=(
            session.get(Person, transfer.from_person_id)
            if transfer.from_person_id
            else None
        ),
        to_person=(
            session.get(Person, transfer.to_person_id)
            if transfer.to_person_id
            else None
        ),
        from_authority_name=_authority_name(transfer.from_authority_id),
        to_authority_name=_authority_name(transfer.to_authority_id),
        documents=_documents_for(session, EntityType.ownership_transfer, transfer.id),
        signature_requests=signature_requests,
        required_documents=[d.value for d in ownership_service.required_documents(transfer)],
        documents_complete=ownership_service.has_all_documents(session, transfer),
    )
