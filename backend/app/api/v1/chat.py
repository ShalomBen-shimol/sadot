"""Chatbot API: a public message endpoint (web widget / WhatsApp bridge) plus
admin endpoints to review conversations and tune the bot."""
from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import select

from app.api.deps import AdminUser, SessionDep
from app.models.chat import BotConfig, ChatMessage, Conversation
from app.schemas.entities import (
    BotConfigRead,
    BotConfigUpdate,
    ChatMessageIn,
    ChatReply,
)
from app.services import chatbot as chatbot_service

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
    cfg = chatbot_service.get_active_bot_config(session)
    return BotConfigRead(
        version=cfg.version, persona=cfg.persona, knowledgebase=cfg.knowledgebase, model=cfg.model
    )


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
    return BotConfigRead(
        version=cfg.version, persona=cfg.persona, knowledgebase=cfg.knowledgebase, model=cfg.model
    )
