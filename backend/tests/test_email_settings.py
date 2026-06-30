"""Admin email-settings API + provider selection.

Covers: the password is encrypted at rest and never returned; PUT keeps the
password when omitted and clears it on ""; an enabled config makes
get_email_provider() return the real SMTP provider; the test endpoint reports
failure cleanly when sending can't connect.
"""
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.adapters.email import MockEmailProvider, SmtpEmailProvider, get_email_provider
from app.core.crypto import decrypt, encrypt


def test_crypto_roundtrip():
    assert decrypt(encrypt("hunter2 app pw")) == "hunter2 app pw"
    assert decrypt("not-a-valid-token") is None


def test_email_settings_requires_admin(client: TestClient):
    assert client.get("/api/v1/integrations/email").status_code == 401


def test_put_encrypts_and_never_leaks_password(client: TestClient, auth: dict[str, str]):
    r = client.put(
        "/api/v1/integrations/email",
        json={"username": "basadot@gmail.com", "password": "app-pw-1234", "enabled": True},
        headers=auth,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "password" not in body and "password_encrypted" not in body
    assert body["password_set"] is True
    assert body["enabled"] is True
    assert body["username"] == "basadot@gmail.com"


def test_put_keeps_password_when_omitted_and_clears_on_empty(client: TestClient, auth: dict[str, str]):
    client.put(
        "/api/v1/integrations/email",
        json={"username": "a@gmail.com", "password": "secret"},
        headers=auth,
    )
    # Omitting password keeps it.
    kept = client.put("/api/v1/integrations/email", json={"from_name": "פנסיון בשדות"}, headers=auth).json()
    assert kept["password_set"] is True
    assert kept["from_name"] == "פנסיון בשדות"
    # Empty string clears it.
    cleared = client.put("/api/v1/integrations/email", json={"password": ""}, headers=auth).json()
    assert cleared["password_set"] is False


def test_provider_selection_follows_db_config(client: TestClient, auth: dict[str, str], engine):
    # Use a fresh session per check, exactly like production opens one per call.
    # Nothing configured -> mock.
    with Session(engine) as s:
        assert isinstance(get_email_provider(s), MockEmailProvider)

    # Enabled SMTP config -> real provider.
    client.put(
        "/api/v1/integrations/email",
        json={"username": "x@gmail.com", "password": "pw", "enabled": True},
        headers=auth,
    )
    with Session(engine) as s:
        provider = get_email_provider(s)
        assert isinstance(provider, SmtpEmailProvider)
        assert provider.username == "x@gmail.com"

    # Disabled -> falls back to mock even though a password is stored.
    client.put("/api/v1/integrations/email", json={"enabled": False}, headers=auth)
    with Session(engine) as s:
        assert isinstance(get_email_provider(s), MockEmailProvider)


def test_test_endpoint_reports_failure_without_crashing(client: TestClient, auth: dict[str, str]):
    # Points at a non-routable SMTP host so the connection fails fast-ish; the
    # endpoint must return a structured failure, not raise.
    client.put(
        "/api/v1/integrations/email",
        json={"host": "127.0.0.1", "port": 2, "username": "x@gmail.com", "password": "pw"},
        headers=auth,
    )
    r = client.post("/api/v1/integrations/email/test", json={"to": "dest@example.com"}, headers=auth)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "failed"
