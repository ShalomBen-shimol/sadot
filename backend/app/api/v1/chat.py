"""Chatbot API: a public message endpoint (web widget) + WhatsApp webhook, plus
admin endpoints to review conversations and tune the bot."""
from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from sqlmodel import select

from app.adapters import get_messaging_provider
from app.api.deps import AdminUser, SessionDep
from app.core.config import settings
from app.core.logging import logger
from app.models.chat import BotConfig, ChatMessage, Conversation
from app.models.enums import ConversationChannel
from app.schemas.entities import (
    BotConfigPreviewIn,
    BotConfigPreviewOut,
    BotConfigRead,
    BotConfigUpdate,
    ChatMessageIn,
    ChatReply,
)
from app.services import chatbot as chatbot_service


def _read(cfg: BotConfig) -> BotConfigRead:
    return BotConfigRead(
        version=cfg.version,
        persona=cfg.persona,
        knowledgebase=cfg.knowledgebase,
        model=cfg.model,
        provider=chatbot_service.provider_name(),
    )


router = APIRouter(prefix="/chat", tags=["chat"])


# ---------- Public (unauthenticated) ----------
@router.post("/message", response_model=ChatReply)
def post_message(payload: ChatMessageIn, session: SessionDep):
    """Send a visitor message; get the bot's reply. Omit conversation_id to start
    a new thread."""
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="Empty message")
    if payload.conversation_id is not None:
        conv = session.get(Conversation, payload.conversation_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conv = chatbot_service.start_conversation(session)

    reply = chatbot_service.handle_message(session, conv, payload.message.strip())
    session.refresh(conv)
    return ChatReply(conversation_id=conv.id, reply=reply.content, status=conv.status.value)


# ---------- WhatsApp (Meta Cloud API) webhook ----------
@router.get("/whatsapp/webhook", response_class=PlainTextResponse)
def whatsapp_verify(request: Request):
    """Meta verification handshake: echo hub.challenge when the token matches."""
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == settings.whatsapp_verify_token:
        return PlainTextResponse(q.get("hub.challenge") or "")
    raise HTTPException(status_code=403, detail="verification failed")


@router.post("/whatsapp/webhook")
async def whatsapp_inbound(request: Request, session: SessionDep):
    """Receive inbound WhatsApp messages, run the engine, and send the reply back
    via the messaging provider (mock until Meta credentials are wired)."""
    payload = await request.json()
    handled = 0
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                phone = msg.get("from")
                text = (msg.get("text") or {}).get("body")
                if not phone or not text:
                    continue
                conv = chatbot_service.get_or_start_by_external(
                    session, ConversationChannel.whatsapp, phone
                )
                reply = chatbot_service.handle_message(session, conv, text)
                try:
                    get_messaging_provider().send(phone, reply.content)
                except Exception as exc:  # noqa: BLE001 — never fail the webhook
                    logger.warning("[WHATSAPP] reply send failed to %s: %s", phone, exc)
                handled += 1
    return {"status": "ok", "handled": handled}


# ---------- Admin ----------
@router.get("/conversations", response_model=list[Conversation])
def list_conversations(
    session: SessionDep,
    _: AdminUser,
    offset: int = 0,
    limit: int = Query(default=50, le=200),
):
    return session.exec(
        select(Conversation).order_by(Conversation.updated_at.desc()).offset(offset).limit(limit)
    ).all()


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: int, session: SessionDep, _: AdminUser):
    conv = session.get(Conversation, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = session.exec(
        select(ChatMessage).where(ChatMessage.conversation_id == conv.id).order_by(ChatMessage.id)
    ).all()
    return {"conversation": conv, "messages": messages}


@router.get("/bot-config", response_model=BotConfigRead)
def get_bot_config(session: SessionDep, _: AdminUser):
    return _read(chatbot_service.get_active_bot_config(session))


@router.post("/bot-config/preview", response_model=BotConfigPreviewOut)
def preview_bot_config(payload: BotConfigPreviewIn, session: SessionDep, _: AdminUser):
    """Test-sandbox: try candidate persona/knowledgebase against a message without
    saving anything or creating any lead."""
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="Empty message")
    reply = chatbot_service.preview(
        payload.persona, payload.knowledgebase, payload.model, payload.message.strip(), payload.history
    )
    return BotConfigPreviewOut(reply=reply)


@router.put("/bot-config", response_model=BotConfigRead)
def update_bot_config(payload: BotConfigUpdate, session: SessionDep, user: AdminUser):
    """Save a new bot-config version and activate it (previous versions kept for
    rollback). Only the editable persona/knowledgebase/model change — the safety
    scaffold is code-owned."""
    current = chatbot_service.get_active_bot_config(session)
    max_version = session.exec(select(BotConfig).order_by(BotConfig.version.desc())).first()
    new_version = (max_version.version + 1) if max_version else 1

    for existing in session.exec(select(BotConfig).where(BotConfig.is_active == True)).all():  # noqa: E712
        existing.is_active = False
        session.add(existing)

    cfg = BotConfig(
        version=new_version,
        is_active=True,
        persona=payload.persona if payload.persona is not None else current.persona,
        knowledgebase=payload.knowledgebase
        if payload.knowledgebase is not None
        else current.knowledgebase,
        model=payload.model or current.model,
        created_by_user_id=user.id,
    )
    session.add(cfg)
    session.commit()
    session.refresh(cfg)
    return _read(cfg)
