"""Configurable ownership-transfer workflow engine + builder API."""
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.dog import Dog
from app.models.enums import (
    DocumentStatus,
    DocumentType,
    EntityType,
    OwnershipTransferStatus,
    TransferType,
)
from app.models.municipality import Municipality
from app.models.ownership import OwnershipTransfer
from app.models.person import Person
from app.models.support import Document
from app.services import ownership as ownership_service
from app.services import workflow as workflow_service

ADOPTER_DOCS = [
    "ownership_transfer_form",
    "id_card_surrenderer",
    "receiver_approval_form",
    "id_card_receiver",
    "adopter_with_dog_photo",
]


def _seed_transfer(db_session: Session) -> OwnershipTransfer:
    dog = Dog(name="רקס")
    person = Person(first_name="דנה", email="dana@example.com")
    authority = Municipality(city_name="חיפה", email="vet@haifa.example.gov")
    db_session.add_all([dog, person, authority])
    db_session.commit()
    db_session.refresh(dog)
    db_session.refresh(person)
    db_session.refresh(authority)
    t = OwnershipTransfer(
        dog_id=dog.id,
        from_person_id=person.id,
        transfer_type=TransferType.facility_to_adopter,
        to_authority_id=authority.id,
    )
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


def test_workflow_drives_transfer_step_by_step(
    client: TestClient, auth: dict[str, str], db_session: Session
):
    t = _seed_transfer(db_session)
    workflow_service.advance(db_session, t)  # stops at the documents gate

    st = client.get(f"/api/v1/ownership-transfers/{t.id}/workflow", headers=auth).json()
    assert st["current"]["type"] == "documents"
    assert st["blocking"]  # docs missing

    # Provide all required documents.
    for dt in ADOPTER_DOCS:
        db_session.add(
            Document(
                related_entity_type=EntityType.ownership_transfer,
                related_entity_id=t.id,
                document_type=DocumentType(dt),
                status=DocumentStatus.uploaded,
            )
        )
    db_session.commit()

    # Advance: passes the docs gate, stops at the manual email action.
    st = client.post(f"/api/v1/ownership-transfers/{t.id}/advance", headers=auth).json()
    assert st["current"]["type"] == "email"
    assert st["awaiting_action"] is True

    # Fire the email action.
    st = client.post(
        f"/api/v1/ownership-transfers/{t.id}/advance", params={"run_action": True}, headers=auth
    ).json()
    assert st["current"]["type"] == "await_confirmation"
    db_session.refresh(t)
    assert t.status == OwnershipTransferStatus.sent_to_authority
    assert t.next_followup_at is not None

    # Confirmation satisfies the last gate; workflow completes.
    ownership_service.confirm(db_session, t)
    final = workflow_service.status(db_session, t)
    assert final["done"] is True


def test_workflow_builder_config(client: TestClient, auth: dict[str, str]):
    assert client.get("/api/v1/workflows").status_code == 401  # admin only

    types = client.get("/api/v1/workflows/step-types", headers=auth).json()
    assert any(s["type"] == "email" for s in types["step_types"])
    assert "facility_to_adopter" in types["transfer_types"]

    current = client.get("/api/v1/workflows/facility_to_adopter", headers=auth).json()
    base_version = current["version"]
    assert len(current["steps"]) >= 1

    saved = client.put(
        "/api/v1/workflows/facility_to_adopter",
        json={"steps": [{"type": "task", "title": "בדיקה", "config": {"title": "בדיקה", "priority": "high"}}]},
        headers=auth,
    ).json()
    assert saved["version"] == base_version + 1

    got = client.get("/api/v1/workflows/facility_to_adopter", headers=auth).json()
    assert len(got["steps"]) == 1 and got["steps"][0]["type"] == "task"

    bad = client.put("/api/v1/workflows/nope", json={"steps": []}, headers=auth)
    assert bad.status_code == 422
