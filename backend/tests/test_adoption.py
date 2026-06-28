"""Adoption workflow tests: reservation, approval (transfer + signatures),
completion, and the direct-home-adoption variant."""
from sqlmodel import select

from app.models.dog import Dog
from app.models.enums import DogStatus, SignatureType, TransferType
from app.models.ownership import OwnershipTransfer
from app.models.support import SignatureRequest


def _seeded_available_dog_id(client):
    return client.get("/api/v1/public/dogs").json()[0]["id"]


def _new_adopter_id(client, phone="0500000002"):
    r = client.post(
        "/api/v1/public/leads/adoption",
        json={"first_name": "יוסי", "phone": phone, "city": "תל אביב",
              "consent_messages": True, "consent_privacy": True, "home_type": "house"},
    )
    assert r.status_code == 200, r.text
    return r.json()["person_id"]


def _create_case(client, auth, dog_id, adopter_id, **extra):
    r = client.post(
        "/api/v1/adoption-cases", headers=auth,
        json={"dog_id": dog_id, "adopter_person_id": adopter_id, **extra},
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_create_case_reserves_dog(client, auth):
    dog_id = _seeded_available_dog_id(client)
    adopter_id = _new_adopter_id(client)
    _create_case(client, auth, dog_id, adopter_id)
    dog = client.get(f"/api/v1/public/dogs/{dog_id}").json()
    assert dog["status"] == "reserved"


def test_approve_opens_transfer_and_adopter_signature(client, auth, db_session):
    dog_id = _seeded_available_dog_id(client)
    adopter_id = _new_adopter_id(client)
    case = _create_case(client, auth, dog_id, adopter_id)

    r = client.post(f"/api/v1/adoption-cases/{case['id']}/approve", headers=auth)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "waiting_for_signatures"

    transfers = db_session.exec(
        select(OwnershipTransfer).where(OwnershipTransfer.dog_id == dog_id)
    ).all()
    assert len(transfers) == 1
    assert transfers[0].transfer_type == TransferType.facility_to_adopter

    sigs = db_session.exec(
        select(SignatureRequest).where(SignatureRequest.related_entity_id == case["id"])
    ).all()
    types = {s.signature_type for s in sigs}
    assert SignatureType.adopter in types
    # Seeded dog has no current owner -> no surrenderer signature.
    assert SignatureType.surrenderer not in types


def test_complete_marks_dog_adopted_and_sets_owner(client, auth, db_session):
    dog_id = _seeded_available_dog_id(client)
    adopter_id = _new_adopter_id(client)
    case = _create_case(client, auth, dog_id, adopter_id)
    client.post(f"/api/v1/adoption-cases/{case['id']}/approve", headers=auth)

    r = client.post(f"/api/v1/adoption-cases/{case['id']}/complete", headers=auth)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed"

    dog = db_session.get(Dog, dog_id)
    assert dog.status == DogStatus.adopted
    assert dog.current_owner_person_id == adopter_id
    # Adopted dog drops off the public adoption listing.
    assert all(d["id"] != dog_id for d in client.get("/api/v1/public/dogs").json())


def test_direct_home_adoption_includes_surrenderer_signature(client, auth, db_session):
    """A dog still at the owner's home, adopted directly, needs the surrenderer
    (current owner) to sign too, and opens a direct surrenderer->adopter transfer."""
    # Home surrender -> activate so the dog is available and owned by surrenderer.
    sr = client.post(
        "/api/v1/public/leads/surrender",
        json={"first_name": "מוסר", "phone": "0507776655", "city": "יקנעם",
              "surrender_type": "home_subscription", "consent_privacy": True,
              "dog_name": "ג'ינג'ר", "dog_breed": "מעורב"},
    ).json()
    client.post(f"/api/v1/surrender-cases/{sr['case_id']}/activate-home-subscription", headers=auth)
    case_full = client.get(f"/api/v1/surrender-cases/{sr['case_id']}", headers=auth).json()
    dog_id = case_full["dog_id"]

    adopter_id = _new_adopter_id(client, phone="0501230000")
    case = _create_case(client, auth, dog_id, adopter_id, is_direct_home_adoption=True)
    r = client.post(f"/api/v1/adoption-cases/{case['id']}/approve", headers=auth)
    assert r.status_code == 200, r.text

    transfer = db_session.exec(
        select(OwnershipTransfer).where(OwnershipTransfer.dog_id == dog_id)
    ).first()
    assert transfer.transfer_type == TransferType.direct_surrenderer_to_adopter

    sigs = db_session.exec(
        select(SignatureRequest).where(SignatureRequest.related_entity_id == case["id"])
    ).all()
    types = {s.signature_type for s in sigs}
    assert {SignatureType.adopter, SignatureType.surrenderer} <= types


def test_approve_missing_case_404(client, auth):
    assert client.post("/api/v1/adoption-cases/999999/approve", headers=auth).status_code == 404
