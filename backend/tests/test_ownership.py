"""Ownership-transfer + authority follow-up engine tests."""
from datetime import datetime, timedelta, timezone

from sqlmodel import select

from app.models.dog import Dog
from app.models.enums import (
    DocumentType,
    DogStatus,
    EntityType,
    LocationType,
    OwnershipTransferStatus,
    TransferType,
)
from app.models.ownership import OwnershipTransfer
from app.models.person import Person
from app.models.support import Document, Task


def _make_dog(db_session, **kw) -> Dog:
    dog = Dog(name=kw.pop("name", "כלב"), status=kw.pop("status", DogStatus.in_facility), **kw)
    db_session.add(dog)
    db_session.commit()
    db_session.refresh(dog)
    return dog


def _create_transfer(client, auth, dog_id, transfer_type, **extra):
    r = client.post(
        "/api/v1/ownership-transfers", headers=auth,
        json={"dog_id": dog_id, "transfer_type": transfer_type, **extra},
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_required_documents_for_facility_surrender(client, auth, db_session):
    dog = _make_dog(db_session)
    t = _create_transfer(client, auth, dog.id, "surrender_to_facility")
    req = client.get(f"/api/v1/ownership-transfers/{t['id']}/required-documents", headers=auth).json()
    assert set(req["required"]) == {"ownership_transfer_form", "id_card_surrenderer"}
    assert req["complete"] is False


def test_required_documents_for_adopter_transfer(client, auth, db_session):
    dog = _make_dog(db_session)
    t = _create_transfer(client, auth, dog.id, "facility_to_adopter")
    req = client.get(f"/api/v1/ownership-transfers/{t['id']}/required-documents", headers=auth).json()
    assert set(req["required"]) == {
        "ownership_transfer_form", "id_card_surrenderer",
        "receiver_approval_form", "id_card_receiver",
    }


def test_documents_completion_flips_when_all_present(client, auth, db_session):
    dog = _make_dog(db_session)
    t = _create_transfer(client, auth, dog.id, "surrender_to_facility")
    for doc_type in (DocumentType.ownership_transfer_form, DocumentType.id_card_surrenderer):
        db_session.add(Document(
            related_entity_type=EntityType.ownership_transfer,
            related_entity_id=t["id"],
            document_type=doc_type,
            file_url="https://files.example/x",
        ))
    db_session.commit()
    req = client.get(f"/api/v1/ownership-transfers/{t['id']}/required-documents", headers=auth).json()
    assert req["complete"] is True


def test_send_to_authority_schedules_followup_and_task(client, auth, db_session):
    dog = _make_dog(db_session)
    t = _create_transfer(client, auth, dog.id, "surrender_to_facility")
    r = client.post(f"/api/v1/ownership-transfers/{t['id']}/send-to-authority", headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "sent_to_authority"
    assert body["sent_to_authority_at"] is not None
    assert body["next_followup_at"] is not None
    # A follow-up task was opened for this transfer.
    tasks = db_session.exec(
        select(Task).where(
            Task.related_entity_type == EntityType.ownership_transfer,
            Task.related_entity_id == t["id"],
        )
    ).all()
    assert len(tasks) == 1
    assert tasks[0].is_followup is True


def test_due_followup_fires_and_reschedules(client, auth, db_session):
    """The core mechanism: a transfer past its next_followup_at gets a reminder
    task and its follow-up is rescheduled into the future."""
    dog = _make_dog(db_session)
    t = _create_transfer(client, auth, dog.id, "surrender_to_facility")
    client.post(f"/api/v1/ownership-transfers/{t['id']}/send-to-authority", headers=auth)

    # Backdate the follow-up so the sweep considers it due.
    transfer = db_session.get(OwnershipTransfer, t["id"])
    transfer.next_followup_at = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.add(transfer)
    db_session.commit()

    sweep = client.post("/api/v1/ownership-transfers/run-followups", headers=auth).json()
    assert sweep["reminders_created"] == 1

    db_session.refresh(transfer)
    assert transfer.status == OwnershipTransferStatus.followup_required
    # SQLite returns naive datetimes (no tz persisted); normalize before comparing.
    next_at = transfer.next_followup_at
    if next_at.tzinfo is None:
        next_at = next_at.replace(tzinfo=timezone.utc)
    assert next_at > datetime.now(timezone.utc)
    # Two tasks now: the initial follow-up + the reminder.
    tasks = db_session.exec(
        select(Task).where(Task.related_entity_id == t["id"],
                           Task.related_entity_type == EntityType.ownership_transfer)
    ).all()
    assert len(tasks) == 2


def test_confirm_facility_transfer_updates_dog(client, auth, db_session):
    dog = _make_dog(db_session, status=DogStatus.pending_surrender)
    t = _create_transfer(client, auth, dog.id, "surrender_to_facility")
    client.post(f"/api/v1/ownership-transfers/{t['id']}/send-to-authority", headers=auth)
    r = client.post(f"/api/v1/ownership-transfers/{t['id']}/confirm", headers=auth)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "confirmed"
    assert r.json()["next_followup_at"] is None

    db_session.refresh(dog)
    assert dog.status == DogStatus.in_facility
    assert dog.current_location_type == LocationType.facility
    assert dog.current_owner_person_id is None


def test_confirm_adopter_transfer_sets_owner(client, auth, db_session):
    adopter = Person(first_name="מאמץ", phone="0506660000", city="תל אביב")
    db_session.add(adopter)
    db_session.commit()
    db_session.refresh(adopter)
    dog = _make_dog(db_session, status=DogStatus.reserved)
    t = _create_transfer(client, auth, dog.id, "facility_to_adopter", to_person_id=adopter.id)
    client.post(f"/api/v1/ownership-transfers/{t['id']}/send-to-authority", headers=auth)
    client.post(f"/api/v1/ownership-transfers/{t['id']}/confirm", headers=auth)

    db_session.refresh(dog)
    assert dog.status == DogStatus.adopted
    assert dog.current_owner_person_id == adopter.id


def test_stop_halts_followups(client, auth, db_session):
    dog = _make_dog(db_session)
    t = _create_transfer(client, auth, dog.id, "surrender_to_facility")
    client.post(f"/api/v1/ownership-transfers/{t['id']}/send-to-authority", headers=auth)
    r = client.post(f"/api/v1/ownership-transfers/{t['id']}/stop", headers=auth)
    assert r.status_code == 200
    assert r.json()["status"] == "stopped_manually"

    # Even if backdated, a stopped transfer is never swept.
    transfer = db_session.get(OwnershipTransfer, t["id"])
    transfer.next_followup_at = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.add(transfer)
    db_session.commit()
    sweep = client.post("/api/v1/ownership-transfers/run-followups", headers=auth).json()
    assert sweep["reminders_created"] == 0
