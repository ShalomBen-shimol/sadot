"""Chatbot engine (Mock provider): full intake → lead, plus admin endpoints."""
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.chat import BotConfig, ChatMessage, Conversation
from app.models.enums import ConversationStatus, SurrenderType
from app.models.surrender import SurrenderCase


def _send(client: TestClient, message: str, conversation_id: int | None = None) -> dict:
    r = client.post(
        "/api/v1/chat/message",
        json={"message": message, "conversation_id": conversation_id},
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_public_intake_runs_without_auth_and_creates_a_lead(
    client: TestClient, db_session: Session
):
    # No auth header — the public message endpoint must be open.
    first = _send(client, "היי")
    conv_id = first["conversation_id"]
    assert first["status"] == ConversationStatus.active.value
    assert "שמך" in first["reply"]  # greeting asks for the name

    _send(client, "דנה כהן", conv_id)          # owner_name
    _send(client, "050-1234567", conv_id)       # owner_phone
    _send(client, "רקס, לברדור", conv_id)       # dog_name
    _send(client, "עוברים דירה", conv_id)       # reason
    final = _send(client, "מסירה מהבית", conv_id)  # surrender_type -> creates lead

    assert final["status"] == ConversationStatus.lead_created.value

    conv = db_session.get(Conversation, conv_id)
    db_session.refresh(conv)
    assert conv.status == ConversationStatus.lead_created
    assert conv.person_id is not None
    assert conv.surrender_case_id is not None

    case = db_session.get(SurrenderCase, conv.surrender_case_id)
    assert case.surrenderer_person_id == conv.person_id
    # "מהבית" routes to the home-subscription track.
    assert case.surrender_type == SurrenderType.home_subscription
    assert conv.collected.get("owner_name") == "דנה כהן"


def test_admin_can_review_conversations(client: TestClient, auth: dict[str, str]):
    conv_id = _send(client, "שלום")["conversation_id"]
    _send(client, "אבי לוי", conv_id)

    # Requires admin.
    assert client.get("/api/v1/chat/conversations").status_code == 401

    lst = client.get("/api/v1/chat/conversations", headers=auth)
    assert lst.status_code == 200
    assert any(c["id"] == conv_id for c in lst.json())

    detail = client.get(f"/api/v1/chat/conversations/{conv_id}", headers=auth).json()
    assert detail["conversation"]["id"] == conv_id
    roles = [m["role"] for m in detail["messages"]]
    assert "user" in roles and "assistant" in roles


def test_bot_config_get_and_versioned_update(
    client: TestClient, auth: dict[str, str], db_session: Session
):
    current = client.get("/api/v1/chat/bot-config", headers=auth).json()
    assert current["model"] == "claude-opus-4-8"

    updated = client.put(
        "/api/v1/chat/bot-config",
        json={"persona": "טון חם ותומך במיוחד"},
        headers=auth,
    ).json()
    assert updated["persona"] == "טון חם ותומך במיוחד"
    assert updated["version"] == current["version"] + 1

    # Exactly one active config, and it's the new version.
    actives = db_session.exec(select(BotConfig).where(BotConfig.is_active == True)).all()  # noqa: E712
    assert len(actives) == 1
    assert actives[0].version == updated["version"]
