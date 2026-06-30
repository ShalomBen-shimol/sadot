"""PDF form generation + document approval + per-flow required documents."""
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.adapters.storage import get_storage_provider
from app.models.dog import Dog
from app.models.enums import (
    DocumentStatus,
    DocumentType,
    SignatureStatus,
    SurrenderType,
    TransferType,
)
from app.models.ownership import OwnershipTransfer
from app.models.person import Person
from app.models.support import Document, SignatureRequest, Task
from app.models.surrender import SurrenderCase
from app.services import ownership as ownership_service


def _seed_person_dog(db_session: Session) -> tuple[int, int]:
    person = Person(first_name="דנה", last_name="כהן", phone="050-1111111", city="חיפה")
    dog = Dog(name="רקס", breed="לברדור", chip_number="123456789")
    db_session.add(person)
    db_session.add(dog)
    db_session.commit()
    db_session.refresh(person)
    db_session.refresh(dog)
    return person.id, dog.id


def _read_stored(file_url: str) -> bytes:
    key = file_url.split("/media/", 1)[-1]
    return get_storage_provider().read(key)


def test_generate_surrender_form_pdf_and_automation(
    client: TestClient, auth: dict[str, str], db_session: Session
):
    person_id, dog_id = _seed_person_dog(db_session)
    case = SurrenderCase(
        surrenderer_person_id=person_id, dog_id=dog_id, surrender_type=SurrenderType.facility
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    r = client.post(f"/api/v1/surrender-cases/{case.id}/generate-form", headers=auth)
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["document_type"] == DocumentType.surrender_form.value
    assert doc["is_sensitive"] is True
    assert doc["file_url"]
    # A real PDF artifact was produced.
    assert _read_stored(doc["file_url"]).startswith(b"%PDF")

    # Automation: a pending signature request + a follow-up task were opened.
    sigs = db_session.exec(
        select(SignatureRequest).where(SignatureRequest.related_entity_id == case.id)
    ).all()
    assert any(s.status == SignatureStatus.pending for s in sigs)
    tasks = db_session.exec(select(Task).where(Task.related_entity_id == case.id)).all()
    assert len(tasks) >= 1


def test_generate_transfer_form_pdf(client: TestClient, auth: dict[str, str], db_session: Session):
    person_id, dog_id = _seed_person_dog(db_session)
    transfer = OwnershipTransfer(
        dog_id=dog_id, from_person_id=person_id, transfer_type=TransferType.surrender_to_facility
    )
    db_session.add(transfer)
    db_session.commit()
    db_session.refresh(transfer)

    r = client.post(f"/api/v1/ownership-transfers/{transfer.id}/generate-form", headers=auth)
    assert r.status_code == 201, r.text
    assert r.json()["document_type"] == DocumentType.ownership_transfer_form.value
    assert _read_stored(r.json()["file_url"]).startswith(b"%PDF")


def test_document_approve_and_reject(client: TestClient, auth: dict[str, str], db_session: Session):
    person_id, dog_id = _seed_person_dog(db_session)
    case = SurrenderCase(surrenderer_person_id=person_id, dog_id=dog_id)
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    doc = client.post(f"/api/v1/surrender-cases/{case.id}/generate-form", headers=auth).json()

    approved = client.post(f"/api/v1/documents/{doc['id']}/approve", headers=auth)
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == DocumentStatus.approved.value

    rejected = client.post(f"/api/v1/documents/{doc['id']}/reject", headers=auth)
    assert rejected.json()["status"] == DocumentStatus.rejected.value


def test_transfer_required_docs_include_new_owner_photo():
    # Individual-to-individual transfer must require the new-owner-with-dog photo.
    individual = OwnershipTransfer(
        dog_id=1, transfer_type=TransferType.direct_surrenderer_to_adopter
    )
    req = ownership_service.required_documents(individual)
    assert DocumentType.adopter_with_dog_photo in req
    assert DocumentType.id_card_receiver in req

    # Surrender-to-facility does not need the receiver-side docs.
    to_facility = OwnershipTransfer(dog_id=1, transfer_type=TransferType.surrender_to_facility)
    assert DocumentType.adopter_with_dog_photo not in ownership_service.required_documents(to_facility)
