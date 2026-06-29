"""Back-office aggregate case-file endpoints + list filters.

Seeds a small but complete scenario (a surrenderer who owns a dog, an adopter
with a lead and a case, an ownership transfer with documents/signature, plus
cross-cutting documents and a message) and asserts each aggregate returns the
linked data.
"""
from app.models.adoption import AdoptionCase, AdoptionLead
from app.models.dog import Dog, DogPhoto
from app.models.enums import (
    AdoptionStatus,
    DocumentType,
    DogStatus,
    EntityType,
    MessageChannel,
    SignatureType,
    SurrenderStatus,
    TransferType,
)
from app.models.municipality import Municipality
from app.models.ownership import OwnershipTransfer
from app.models.person import Person
from app.models.support import Document, Message, SignatureRequest
from app.models.surrender import SurrenderCase
from sqlmodel import select


def _seed_scenario(client, auth, db_session) -> dict:
    """Create a connected graph of entities and return their ids."""
    surrenderer = Person(first_name="מוסר", last_name="כהן", phone="0501112222", city="חיפה")
    adopter = Person(first_name="מאמץ", last_name="לוי", phone="0503334444", city="תל אביב")
    db_session.add(surrenderer)
    db_session.add(adopter)
    db_session.commit()
    db_session.refresh(surrenderer)
    db_session.refresh(adopter)

    dog = Dog(
        name="ביידי",
        breed="מעורב",
        status=DogStatus.in_facility,
        current_owner_person_id=surrenderer.id,
    )
    db_session.add(dog)
    db_session.commit()
    db_session.refresh(dog)

    db_session.add(DogPhoto(dog_id=dog.id, file_url="https://files.example/photo.jpg", is_primary=True))

    surrender_case = SurrenderCase(
        dog_id=dog.id,
        surrenderer_person_id=surrenderer.id,
        status=SurrenderStatus.waiting_for_documents,
    )
    db_session.add(surrender_case)

    lead = AdoptionLead(person_id=adopter.id, dog_id=dog.id)
    db_session.add(lead)

    adoption_case = AdoptionCase(
        dog_id=dog.id,
        adopter_person_id=adopter.id,
        status=AdoptionStatus.screening,
    )
    db_session.add(adoption_case)
    db_session.commit()
    db_session.refresh(surrender_case)
    db_session.refresh(adoption_case)

    # A message to the surrenderer.
    db_session.add(
        Message(person_id=surrenderer.id, channel=MessageChannel.whatsapp, content="שלום, קיבלנו את הפנייה")
    )
    # A document filed against the person and one against the dog.
    db_session.add(
        Document(
            related_entity_type=EntityType.person,
            related_entity_id=surrenderer.id,
            document_type=DocumentType.id_card_surrenderer,
            file_url="https://files.example/id.pdf",
            is_sensitive=True,
        )
    )
    db_session.add(
        Document(
            related_entity_type=EntityType.dog,
            related_entity_id=dog.id,
            document_type=DocumentType.other,
            file_url="https://files.example/vax.pdf",
        )
    )
    db_session.commit()

    # Ownership transfer via the API so authorities are resolved by city.
    r = client.post(
        "/api/v1/ownership-transfers",
        headers=auth,
        json={
            "dog_id": dog.id,
            "from_person_id": surrenderer.id,
            "to_person_id": adopter.id,
            "transfer_type": TransferType.facility_to_adopter.value,
        },
    )
    assert r.status_code == 201, r.text
    transfer_id = r.json()["id"]

    # Attach two (distinct) authorities so the detail endpoint can resolve names.
    transfer = db_session.get(OwnershipTransfer, transfer_id)
    munis = db_session.exec(select(Municipality).limit(2)).all()
    transfer.from_authority_id = munis[0].id
    transfer.to_authority_id = munis[1].id
    db_session.add(transfer)
    db_session.commit()

    # Documents + signature against the transfer.
    for doc_type in (
        DocumentType.ownership_transfer_form,
        DocumentType.id_card_surrenderer,
        DocumentType.receiver_approval_form,
        DocumentType.id_card_receiver,
    ):
        db_session.add(
            Document(
                related_entity_type=EntityType.ownership_transfer,
                related_entity_id=transfer_id,
                document_type=doc_type,
                file_url="https://files.example/x.pdf",
            )
        )
    db_session.add(
        SignatureRequest(
            related_entity_type=EntityType.ownership_transfer,
            related_entity_id=transfer_id,
            signer_person_id=adopter.id,
            signature_type=SignatureType.adopter,
        )
    )
    db_session.commit()

    return {
        "surrenderer_id": surrenderer.id,
        "adopter_id": adopter.id,
        "dog_id": dog.id,
        "surrender_case_id": surrender_case.id,
        "adoption_case_id": adoption_case.id,
        "lead_id": lead.id,
        "transfer_id": transfer_id,
    }


# ---------- person file ----------
def test_person_file_for_surrenderer(client, auth, db_session):
    ids = _seed_scenario(client, auth, db_session)
    r = client.get(f"/api/v1/people/{ids['surrenderer_id']}/file", headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["person"]["id"] == ids["surrenderer_id"]
    assert [d["id"] for d in body["dogs_owned"]] == [ids["dog_id"]]
    assert [c["id"] for c in body["surrender_cases"]] == [ids["surrender_case_id"]]
    assert len(body["documents"]) == 1
    assert body["documents"][0]["document_type"] == DocumentType.id_card_surrenderer.value
    assert len(body["recent_messages"]) == 1
    # The surrenderer has no adoption activity.
    assert body["adoption_cases"] == []
    assert body["adoption_leads"] == []


def test_person_file_for_adopter(client, auth, db_session):
    ids = _seed_scenario(client, auth, db_session)
    r = client.get(f"/api/v1/people/{ids['adopter_id']}/file", headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert [c["id"] for c in body["adoption_cases"]] == [ids["adoption_case_id"]]
    assert [lead["id"] for lead in body["adoption_leads"]] == [ids["lead_id"]]
    assert body["dogs_owned"] == []


def test_person_file_404(client, auth):
    r = client.get("/api/v1/people/999999/file", headers=auth)
    assert r.status_code == 404


# ---------- dog file ----------
def test_dog_file_aggregates_everything(client, auth, db_session):
    ids = _seed_scenario(client, auth, db_session)
    r = client.get(f"/api/v1/dogs/{ids['dog_id']}/file", headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["dog"]["id"] == ids["dog_id"]
    assert body["current_owner"] is not None
    assert body["current_owner"]["id"] == ids["surrenderer_id"]
    assert [c["id"] for c in body["surrender_cases"]] == [ids["surrender_case_id"]]
    assert [c["id"] for c in body["adoption_cases"]] == [ids["adoption_case_id"]]
    assert [lead["id"] for lead in body["adoption_leads"]] == [ids["lead_id"]]
    assert [t["id"] for t in body["ownership_transfers"]] == [ids["transfer_id"]]
    assert len(body["photos"]) == 1
    assert len(body["documents"]) == 1


def test_dog_file_404(client, auth):
    r = client.get("/api/v1/dogs/999999/file", headers=auth)
    assert r.status_code == 404


# ---------- ownership transfer detail ----------
def test_transfer_detail_resolves_authorities_and_docs(client, auth, db_session):
    ids = _seed_scenario(client, auth, db_session)
    r = client.get(f"/api/v1/ownership-transfers/{ids['transfer_id']}/detail", headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["transfer"]["id"] == ids["transfer_id"]
    assert body["dog"]["id"] == ids["dog_id"]
    assert body["from_person"]["id"] == ids["surrenderer_id"]
    assert body["to_person"]["id"] == ids["adopter_id"]
    # Authority names are resolved from the attached authorities.
    assert body["from_authority_name"]
    assert body["to_authority_name"]
    assert body["from_authority_name"] != body["to_authority_name"]
    assert len(body["signature_requests"]) == 1
    assert len(body["documents"]) == 4
    # facility_to_adopter requires all four document types -> complete.
    assert set(body["required_documents"]) == {
        "ownership_transfer_form",
        "id_card_surrenderer",
        "receiver_approval_form",
        "id_card_receiver",
    }
    assert body["documents_complete"] is True


def test_transfer_detail_404(client, auth):
    r = client.get("/api/v1/ownership-transfers/999999/detail", headers=auth)
    assert r.status_code == 404


# ---------- list filters ----------
def test_surrender_cases_status_filter(client, auth, db_session):
    ids = _seed_scenario(client, auth, db_session)
    # Seeded case is waiting_for_documents.
    r = client.get("/api/v1/surrender-cases?status=waiting_for_documents", headers=auth)
    assert r.status_code == 200, r.text
    returned = [c["id"] for c in r.json()]
    assert ids["surrender_case_id"] in returned
    # A different status returns none of our cases.
    r = client.get("/api/v1/surrender-cases?status=completed", headers=auth)
    assert ids["surrender_case_id"] not in [c["id"] for c in r.json()]


def test_adoption_cases_status_filter(client, auth, db_session):
    ids = _seed_scenario(client, auth, db_session)
    r = client.get("/api/v1/adoption-cases?status=screening", headers=auth)
    assert r.status_code == 200, r.text
    assert ids["adoption_case_id"] in [c["id"] for c in r.json()]
    r = client.get("/api/v1/adoption-cases?status=completed", headers=auth)
    assert ids["adoption_case_id"] not in [c["id"] for c in r.json()]


def test_tasks_status_and_followup_filters(client, auth, db_session):
    ids = _seed_scenario(client, auth, db_session)
    # Sending the transfer to the authority opens an is_followup task (status=open).
    r = client.post(
        f"/api/v1/ownership-transfers/{ids['transfer_id']}/send-to-authority", headers=auth
    )
    assert r.status_code == 200, r.text

    # Also create a plain, non-followup task.
    r = client.post(
        "/api/v1/tasks", headers=auth, json={"title": "משימה ידנית"}
    )
    assert r.status_code == 201, r.text

    open_followups = client.get("/api/v1/tasks?status=open&is_followup=true", headers=auth).json()
    assert len(open_followups) >= 1
    assert all(t["is_followup"] is True and t["status"] == "open" for t in open_followups)

    non_followups = client.get("/api/v1/tasks?is_followup=false", headers=auth).json()
    assert all(t["is_followup"] is False for t in non_followups)
    assert any(t["title"] == "משימה ידנית" for t in non_followups)


def test_tasks_invalid_filter_value_returns_422(client, auth):
    r = client.get("/api/v1/tasks?status=not_a_status", headers=auth)
    assert r.status_code == 422
