"""Auth, public-privacy and dashboard tests."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_success_and_me(client):
    r = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@sadot.local", "password": "admin1234"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "admin@sadot.local"
    assert me.json()["role"] == "admin"


def test_login_wrong_password(client):
    r = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@sadot.local", "password": "wrong"},
    )
    assert r.status_code == 401


def test_protected_route_requires_auth(client):
    assert client.get("/api/v1/surrender-cases").status_code == 401
    assert client.get("/api/v1/dashboard/summary").status_code == 401


def test_invalid_token_rejected(client):
    r = client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert r.status_code == 401


def test_public_dogs_listing_hides_sensitive_fields(client):
    dogs = client.get("/api/v1/public/dogs").json()
    assert len(dogs) >= 1
    sensitive = {"chip_number", "internal_notes", "medical_notes",
                 "current_owner_person_id", "behavior_notes"}
    for dog in dogs:
        assert sensitive.isdisjoint(dog.keys()), dog


def test_public_dog_detail_404_for_non_listable(client, db_session):
    from app.models.dog import Dog
    from app.models.enums import DogStatus

    dog = Dog(name="חבוי", status=DogStatus.draft)
    db_session.add(dog)
    db_session.commit()
    db_session.refresh(dog)
    assert client.get(f"/api/v1/public/dogs/{dog.id}").status_code == 404


def test_surrender_lead_requires_privacy_consent(client):
    r = client.post(
        "/api/v1/public/leads/surrender",
        json={"first_name": "א", "phone": "0501112222",
              "surrender_type": "facility", "consent_privacy": False},
    )
    assert r.status_code == 422


def test_adoption_lead_requires_privacy_consent(client):
    r = client.post(
        "/api/v1/public/leads/adoption",
        json={"first_name": "ב", "phone": "0503334444", "consent_privacy": False},
    )
    assert r.status_code == 422


def test_dashboard_summary_shape(client, auth):
    summary = client.get("/api/v1/dashboard/summary", headers=auth).json()
    for key in ("dogs_total", "dogs_available", "dogs_adopted",
                "surrender_cases", "adoption_cases", "open_tasks",
                "transfers_awaiting_authority"):
        assert key in summary, summary
    # Two demo dogs are seeded, both available.
    assert summary["dogs_available"] >= 2
