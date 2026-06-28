"""Surrender workflow tests: home subscription, credit accrual, conversion,
facility transfer, and guard rails."""
import pytest


def _open_home_surrender(client, phone="0500000001", dog_name="בובי"):
    r = client.post(
        "/api/v1/public/leads/surrender",
        json={
            "first_name": "דנה", "phone": phone, "city": "חיפה",
            "surrender_type": "home_subscription", "consent_privacy": True,
            "dog_name": dog_name, "dog_breed": "מעורב", "dog_age": 3,
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["case_id"]


def test_intake_opens_case_and_draft_dog(client, auth):
    case_id = _open_home_surrender(client)
    case = client.get(f"/api/v1/surrender-cases/{case_id}", headers=auth).json()
    assert case["surrender_type"] == "home_subscription"
    assert case["status"] == "new_lead"
    assert case["monthly_price"] == 1000
    assert case["total_required_amount"] == 7200
    # Dog created by intake should NOT be publicly listed yet (status draft).
    assert all(d["id"] != case["dog_id"] for d in client.get("/api/v1/public/dogs").json())


def test_activate_home_subscription_lists_dog_and_charges_month_one(client, auth):
    case_id = _open_home_surrender(client)
    r = client.post(f"/api/v1/surrender-cases/{case_id}/activate-home-subscription", headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "active_home_subscription"
    assert body["accumulated_credit"] == 1000
    # Dog is now available for adoption, located at home.
    dog = client.get(f"/api/v1/public/dogs/{body['dog_id']}").json()
    assert dog["status"] == "available_for_adoption"
    assert dog["current_location_type"] == "home"


def test_credit_accrues_to_7000_over_seven_months(client, auth):
    case_id = _open_home_surrender(client)
    client.post(f"/api/v1/surrender-cases/{case_id}/activate-home-subscription", headers=auth)
    for _ in range(6):
        r = client.post(f"/api/v1/surrender-cases/{case_id}/charge-month", headers=auth)
        assert r.status_code == 200, r.text
    case = client.get(f"/api/v1/surrender-cases/{case_id}", headers=auth).json()
    assert case["accumulated_credit"] == 7000
    payments = client.get(f"/api/v1/surrender-cases/{case_id}/payments", headers=auth).json()
    assert len(payments) == 7
    assert [p["month_index"] for p in payments] == [1, 2, 3, 4, 5, 6, 7]
    assert all(p["status"] == "paid" for p in payments)


def test_convert_home_to_facility_opens_transfer(client, auth):
    case_id = _open_home_surrender(client)
    client.post(f"/api/v1/surrender-cases/{case_id}/activate-home-subscription", headers=auth)
    r = client.post(f"/api/v1/surrender-cases/{case_id}/convert-to-facility", headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ownership_transfer_id"] is not None
    case = client.get(f"/api/v1/surrender-cases/{case_id}", headers=auth).json()
    assert case["surrender_type"] == "facility"
    assert case["status"] == "ownership_transfer_in_progress"
    # The opened transfer is a surrender-to-facility transfer.
    t = client.get(f"/api/v1/ownership-transfers/{body['ownership_transfer_id']}", headers=auth).json()
    assert t["transfer_type"] == "surrender_to_facility"


def test_activate_rejects_non_home_subscription_case(client, auth):
    # Open a plain facility surrender via the public intake.
    r = client.post(
        "/api/v1/public/leads/surrender",
        json={"first_name": "רון", "phone": "0509998877", "city": "חיפה",
              "surrender_type": "facility", "consent_privacy": True, "dog_name": "מקס"},
    )
    case_id = r.json()["case_id"]
    r = client.post(f"/api/v1/surrender-cases/{case_id}/activate-home-subscription", headers=auth)
    assert r.status_code == 422


def test_actions_on_missing_case_404(client, auth):
    assert client.get("/api/v1/surrender-cases/999999", headers=auth).status_code == 404
    assert client.post(
        "/api/v1/surrender-cases/999999/activate-home-subscription", headers=auth
    ).status_code == 404


def test_start_facility_transfer_resolves_surrenderer_authority(client, auth, db_session):
    """The opened transfer's from_authority is resolved from the surrenderer's city."""
    case_id = _open_home_surrender(client)  # city = חיפה (seeded municipality)
    r = client.post(f"/api/v1/surrender-cases/{case_id}/start-facility-transfer", headers=auth)
    assert r.status_code == 200, r.text
    tid = r.json()["ownership_transfer_id"]
    t = client.get(f"/api/v1/ownership-transfers/{tid}", headers=auth).json()
    assert t["from_authority_id"] is not None
