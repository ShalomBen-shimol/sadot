"""Signature mock lifecycle tests: list per entity, mark each signed via the
mock provider callback, and assert the adoption case only advances from
waiting_for_signatures to waiting_for_documents after the last signature."""
from app.models.enums import SignatureStatus


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


def _approved_case(client, auth, **extra):
    dog_id = _seeded_available_dog_id(client)
    adopter_id = _new_adopter_id(client)
    r = client.post(
        "/api/v1/adoption-cases", headers=auth,
        json={"dog_id": dog_id, "adopter_person_id": adopter_id, **extra},
    )
    assert r.status_code == 201, r.text
    case = r.json()
    r = client.post(f"/api/v1/adoption-cases/{case['id']}/approve", headers=auth)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "waiting_for_signatures"
    return case


def test_list_signatures_filtered_by_entity(client, auth):
    case = _approved_case(client, auth)
    r = client.get(
        "/api/v1/signatures",
        headers=auth,
        params={"entity_type": "adoption_case", "entity_id": case["id"]},
    )
    assert r.status_code == 200, r.text
    sigs = r.json()
    # Seeded dog has no current owner -> only the adopter signature.
    assert len(sigs) == 1
    assert all(s["related_entity_id"] == case["id"] for s in sigs)
    assert all(s["status"] != "signed" for s in sigs)


def test_signatures_require_auth(client):
    assert client.get("/api/v1/signatures").status_code == 401


def test_mark_signed_sets_status_and_signed_at(client, auth):
    case = _approved_case(client, auth)
    sig = client.get(
        "/api/v1/signatures", headers=auth,
        params={"entity_type": "adoption_case", "entity_id": case["id"]},
    ).json()[0]

    r = client.post(f"/api/v1/signatures/{sig['id']}/mark-signed", headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "signed"
    assert body["signed_at"] is not None


def test_mark_signed_missing_404(client, auth):
    assert client.post("/api/v1/signatures/999999/mark-signed", headers=auth).status_code == 404


def test_case_advances_only_after_last_signature(client, auth, db_session):
    """Direct home adoption has two signatures (adopter + surrenderer). The case
    must stay in waiting_for_signatures until BOTH are signed."""
    from app.models.adoption import AdoptionCase
    from app.models.enums import AdoptionStatus

    # Home surrender -> activate so the dog is owned by the surrenderer.
    sr = client.post(
        "/api/v1/public/leads/surrender",
        json={"first_name": "מוסר", "phone": "0507776655", "city": "יקנעם",
              "surrender_type": "home_subscription", "consent_privacy": True,
              "dog_name": "ג'ינג'ר", "dog_breed": "מעורב"},
    ).json()
    client.post(
        f"/api/v1/surrender-cases/{sr['case_id']}/activate-home-subscription", headers=auth
    )
    dog_id = client.get(
        f"/api/v1/surrender-cases/{sr['case_id']}", headers=auth
    ).json()["dog_id"]

    adopter_id = _new_adopter_id(client, phone="0501230000")
    r = client.post(
        "/api/v1/adoption-cases", headers=auth,
        json={"dog_id": dog_id, "adopter_person_id": adopter_id,
              "is_direct_home_adoption": True},
    )
    assert r.status_code == 201, r.text
    case = r.json()
    assert client.post(
        f"/api/v1/adoption-cases/{case['id']}/approve", headers=auth
    ).status_code == 200

    sigs = client.get(
        "/api/v1/signatures", headers=auth,
        params={"entity_type": "adoption_case", "entity_id": case["id"]},
    ).json()
    assert len(sigs) == 2

    # First signature: case must NOT advance yet.
    client.post(f"/api/v1/signatures/{sigs[0]['id']}/mark-signed", headers=auth)
    db_session.expire_all()
    case_obj = db_session.get(AdoptionCase, case["id"])
    assert case_obj.status == AdoptionStatus.waiting_for_signatures

    # Last signature: case advances to waiting_for_documents.
    client.post(f"/api/v1/signatures/{sigs[1]['id']}/mark-signed", headers=auth)
    db_session.expire_all()
    case_obj = db_session.get(AdoptionCase, case["id"])
    assert case_obj.status == AdoptionStatus.waiting_for_documents


def test_single_signature_advances_case(client, auth, db_session):
    from app.models.adoption import AdoptionCase
    from app.models.enums import AdoptionStatus

    case = _approved_case(client, auth)
    sig = client.get(
        "/api/v1/signatures", headers=auth,
        params={"entity_type": "adoption_case", "entity_id": case["id"]},
    ).json()[0]
    assert sig["status"] != SignatureStatus.signed.value

    client.post(f"/api/v1/signatures/{sig['id']}/mark-signed", headers=auth)
    db_session.expire_all()
    case_obj = db_session.get(AdoptionCase, case["id"])
    assert case_obj.status == AdoptionStatus.waiting_for_documents
