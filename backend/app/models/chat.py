"""AI chatbot: conversations, their messages, and the owner-editable bot config."""
from datetime import datetime, timezone

from sqlalchemy import Column
from sqlalchemy import JSON as SA_JSON
from sqlmodel import Field, SQLModel

from app.models.enums import ConversationChannel, ConversationGoal, ConversationStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Conversation(SQLModel, table=True):
    """A single chat thread with a visitor (web widget or WhatsApp).

    A web visitor has no Person until enough detail is gathered, so this is kept
    separate from the person-centric Message/notification model. `collected` holds
    the structured fields the bot has gathered toward a "well-cooked" lead."""
    __tablename__ = "conversations"

    id: int | None = Field(default=None, primary_key=True)
    channel: ConversationChannel = Field(default=ConversationChannel.web, index=True)
    goal: ConversationGoal = Field(default=ConversationGoal.surrender)
    status: ConversationStatus = Field(default=ConversationStatus.active, index=True)
    # WhatsApp phone or the web session token — how we re-find an existing thread.
    external_id: str | None = Field(default=None, index=True)
    person_id: int | None = Field(default=None, foreign_key="people.id", index=True)
    surrender_case_id: int | None = Field(
        default=None, foreign_key="surrender_cases.id", index=True
    )
    collected: dict = Field(default_factory=dict, sa_column=Column(SA_JSON))
    escalated: bool = Field(default=False, index=True)
    summary: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class ChatMessage(SQLModel, table=True):
    """One turn in a Conversation. `role` mirrors the LLM roles."""
    __tablename__ = "chat_messages"

    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversations.id", index=True)
    role: str = Field(default="user")  # user | assistant | system | tool
    content: str
    tool_name: str | None = None  # set when the assistant invoked a tool
    created_at: datetime = Field(default_factory=_utcnow)


class BotConfig(SQLModel, table=True):
    """Owner-editable bot behavior. Versioned: each save is a new row; exactly one
    is active. The editable persona + knowledgebase are composed INTO a fixed,
    non-editable safety scaffold at runtime (see services/chatbot.py)."""
    __tablename__ = "bot_configs"

    id: int | None = Field(default=None, primary_key=True)
    version: int = Field(default=1, index=True)
    is_active: bool = Field(default=False, index=True)
    # The owner's "persona / policy" instructions (tone, what to emphasize).
    persona: str = Field(default="")
    # Reference snippets the bot may rely on (pricing, rules, FAQs).
    knowledgebase: str = Field(default="")
    model: str = Field(default="claude-opus-4-8")
    created_by_user_id: int | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=_utcnow)
