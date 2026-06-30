"""PATCH semantics: an explicitly-sent field is applied, including null, so a
value can be cleared (regression for CRUDRepository.update skipping None)."""
from fastapi.testclient import TestClient


def test_patch_can_clear_a_field(client: TestClient, auth: dict[str, str]):
    created = client.post(
        "/api/v1/municipalities",
        json={"city_name": "בדיקה", "email": "vet@example.com", "phone": "03-1234567"},
        headers=auth,
    )
    assert created.status_code == 201, created.text
    mid = created.json()["id"]
    assert created.json()["email"] == "vet@example.com"

    # Explicit null must clear the field...
    patched = client.patch(
        f"/api/v1/municipalities/{mid}", json={"email": None}, headers=auth
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["email"] is None
    # ...and not touch fields that were not sent.
    assert patched.json()["phone"] == "03-1234567"

    # And it must persist.
    got = client.get(f"/api/v1/municipalities/{mid}", headers=auth)
    assert got.json()["email"] is None
    assert got.json()["phone"] == "03-1234567"


def test_patch_omitted_field_is_unchanged(client: TestClient, auth: dict[str, str]):
    created = client.post(
        "/api/v1/municipalities",
        json={"city_name": "בדיקה2", "email": "keep@example.com"},
        headers=auth,
    ).json()
    mid = created["id"]
    # Send only phone; email must be left as-is.
    patched = client.patch(
        f"/api/v1/municipalities/{mid}", json={"phone": "050-0000000"}, headers=auth
    ).json()
    assert patched["email"] == "keep@example.com"
    assert patched["phone"] == "050-0000000"
