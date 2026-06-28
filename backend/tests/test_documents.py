"""Document upload tests: auth gating, storage adapter persistence, audit log,
listing, and the sensitive flag."""
from pathlib import Path

import pytest
from sqlmodel import select

from app.core.config import settings
from app.models.support import AuditLog, Document


@pytest.fixture(name="media_root")
def media_root_fixture(tmp_path, monkeypatch) -> Path:
    """Point the local storage adapter at an isolated temp dir per test."""
    root = tmp_path / "media"
    monkeypatch.setattr(settings, "media_root", str(root))
    return root


def _upload(client, headers, *, entity_type="surrender_case", entity_id=1,
            document_type="id_card_surrenderer", is_sensitive=True,
            content=b"hello-bytes", filename="id.jpg"):
    return client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={
            "related_entity_type": entity_type,
            "related_entity_id": entity_id,
            "document_type": document_type,
            "is_sensitive": str(is_sensitive).lower(),
        },
        files={"file": (filename, content, "image/jpeg")},
    )


def test_upload_requires_auth(client, media_root):
    r = _upload(client, headers={})
    assert r.status_code == 401


def test_list_requires_auth(client):
    assert client.get("/api/v1/documents").status_code == 401


def test_upload_stores_file_creates_row_and_audit(client, auth, media_root, db_session):
    r = _upload(client, auth, content=b"the-file-bytes")
    assert r.status_code == 201, r.text
    body = r.json()

    assert body["id"] is not None
    assert body["related_entity_type"] == "surrender_case"
    assert body["related_entity_id"] == 1
    assert body["document_type"] == "id_card_surrenderer"
    assert body["status"] == "uploaded"
    assert body["is_sensitive"] is True
    assert body["uploaded_by_user_id"] is not None
    assert body["file_url"].startswith("/media/surrender_case/1/")

    # File physically written under the configured media root.
    key = body["file_url"].removeprefix("/media/")
    stored = media_root / key
    assert stored.exists()
    assert stored.read_bytes() == b"the-file-bytes"

    # Document row persisted.
    doc = db_session.get(Document, body["id"])
    assert doc is not None
    assert doc.file_url == body["file_url"]

    # Audit entry recorded for the sensitive upload.
    logs = db_session.exec(
        select(AuditLog).where(AuditLog.action == "document.upload")
    ).all()
    assert len(logs) == 1
    assert logs[0].entity_type == "surrender_case"
    assert logs[0].entity_id == 1
    assert str(body["id"]) in (logs[0].metadata_json or "")


def test_list_returns_uploaded_document_filtered_by_entity(client, auth, media_root):
    _upload(client, auth, entity_type="surrender_case", entity_id=42)
    _upload(client, auth, entity_type="adoption_case", entity_id=99)

    r = client.get(
        "/api/v1/documents",
        headers=auth,
        params={"entity_type": "surrender_case", "entity_id": 42},
    )
    assert r.status_code == 200, r.text
    items = r.json()
    assert len(items) == 1
    assert items[0]["related_entity_type"] == "surrender_case"
    assert items[0]["related_entity_id"] == 42


def test_sensitive_flag_respected(client, auth, media_root):
    r_sensitive = _upload(client, auth, document_type="id_card_receiver", is_sensitive=True)
    r_public = _upload(
        client, auth, document_type="adopter_with_dog_photo",
        is_sensitive=False, filename="photo.png",
    )
    assert r_sensitive.json()["is_sensitive"] is True
    assert r_public.json()["is_sensitive"] is False


def test_empty_file_rejected(client, auth, media_root):
    r = _upload(client, auth, content=b"")
    assert r.status_code == 422
