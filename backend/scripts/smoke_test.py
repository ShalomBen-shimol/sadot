"""End-to-end smoke test using FastAPI TestClient (no server needed)."""
from fastapi.testclient import TestClient

from app.main import app


def run(client: TestClient) -> None:
    # Health
    assert client.get("/health").json()["status"] == "ok"

    # Login as seeded admin
    r = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@sadot.local", "password": "admin1234"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    # Public adoption listing (seeded dogs)
    dogs = client.get("/api/v1/public/dogs").json()
    assert len(dogs) >= 1, dogs
    print(f"public dogs available: {len(dogs)}")
    # Ensure no sensitive fields leaked
    assert "internal_notes" not in dogs[0]
    assert "chip_number" not in dogs[0]

    # Public surrender lead (home subscription)
    r = client.post(
        "/api/v1/public/leads/surrender",
        json={
            "first_name": "דנה", "phone": "0500000001", "city": "חיפה",
            "surrender_type": "home_subscription", "consent_privacy": True,
            "dog_name": "בּוֹבּי", "dog_breed": "מעורב", "dog_age": 3,
        },
    )
    assert r.status_code == 200, r.text
    case_id = r.json()["case_id"]
    print(f"surrender case opened: {case_id}")

    # Activate home subscription -> month 1 payment, dog becomes available
    r = client.post(f"/api/v1/surrender-cases/{case_id}/activate-home-subscription", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "active_home_subscription"
    assert r.json()["accumulated_credit"] == 1000

    # Charge 6 more months -> credit reaches 7000
    for _ in range(6):
        client.post(f"/api/v1/surrender-cases/{case_id}/charge-month", headers=h)
    case = client.get(f"/api/v1/surrender-cases/{case_id}", headers=h).json()
    assert case["accumulated_credit"] == 7000, case
    print(f"accumulated credit after 7 months: {case['accumulated_credit']}")

    # Public adoption lead
    r = client.post(
        "/api/v1/public/leads/adoption",
        json={
            "first_name": "יוסי", "phone": "0500000002", "city": "תל אביב",
            "consent_messages": True, "consent_privacy": True, "home_type": "house",
        },
    )
    assert r.status_code == 200, r.text
    print(f"adoption lead person: {r.json()['person_id']}")

    # Adoption case on the first available dog -> approve -> complete
    dog_id = dogs[0]["id"]
    adopter_id = r.json()["person_id"]
    r = client.post(
        "/api/v1/adoption-cases",
        headers=h,
        json={"dog_id": dog_id, "adopter_person_id": adopter_id},
    )
    assert r.status_code == 201, r.text
    acase_id = r.json()["id"]

    r = client.post(f"/api/v1/adoption-cases/{acase_id}/approve", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "waiting_for_signatures"

    r = client.post(f"/api/v1/adoption-cases/{acase_id}/complete", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed"
    print(f"adoption case {acase_id} completed; dog {dog_id} adopted")

    # Ownership transfer follow-up: open + send + run sweep
    ots = client.get("/api/v1/ownership-transfers", headers=h).json()
    print(f"ownership transfers created: {len(ots)}")
    if ots:
        tid = ots[0]["id"]
        client.post(f"/api/v1/ownership-transfers/{tid}/send-to-authority", headers=h)
        sweep = client.post("/api/v1/ownership-transfers/run-followups", headers=h).json()
        print(f"followup sweep: {sweep}")

    # Dashboard summary
    summary = client.get("/api/v1/dashboard/summary", headers=h).json()
    print("dashboard summary:", summary)

    print("\nSMOKE_TEST_OK")


def main() -> None:
    # Context manager triggers FastAPI lifespan (init_db + seed).
    with TestClient(app) as client:
        run(client)


if __name__ == "__main__":
    main()
