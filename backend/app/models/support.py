"""Cross-cutting entities: documents, signatures, tasks, messages, audit log."""
from datetime import date, datetime

from sqlmodel import Field, SQLModel

from app.models.base import utcnow
from app.models.enums import (
    DocumentStatus,
    DocumentType,
    EntityType,
    MessageChannel,
    MessageDirection,
    MessageStatus,
    SignatureStatus,
    SignatureType,
    TaskPriority,
    TaskStatus,
)


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: int | None = Field(default=None, primary_key=True)
    related_entity_type: EntityType = Field(index=True)
    related_entity_id: int = Field(index=True)
    document_type: DocumentType
    file_url: str | None = None
    uploaded_by_user_id: int | None = Field(default=None, foreign_key="users.id")
    uploaded_by_person_id: int | None = Field(default=None, foreign_key="people.id")
    status: DocumentStatus = Field(default=DocumentStatus.pending)
    # True for ID cards / signed docs — gated behind audit logging.
    is_sensitive: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utcnow)


class SignatureRequest(SQLModel, table=True):
    __tablename__ = "signature_requests"

    id: int | None = Field(default=None, primary_key=True)
    related_entity_type: EntityType = Field(index=True)
    related_entity_id: int = Field(index=True)
    signer_person_id: int = Field(foreign_key="people.id")
    signature_type: SignatureType
    status: SignatureStatus = Field(default=SignatureStatus.pending)
    sign_url: str | None = None
    signed_at: datetime | None = None
    provider_reference: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    related_entity_type: EntityType | None = Field(default=None, index=True)
    related_entity_id: int | None = Field(default=None, index=True)
    assigned_to_user_id: int | None = Field(default=None, foreign_key="users.id")
    due_date: date | None = Field(default=None, index=True)
    status: TaskStatus = Field(default=TaskStatus.open, index=True)
    priority: TaskPriority = Field(default=TaskPriority.normal)
    # Marks auto-generated follow-up tasks vs manual tasks.
    is_followup: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utcnow)


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: int | None = Field(default=None, primary_key=True)
    person_id: int | None = Field(default=None, foreign_key="people.id", index=True)
    channel: MessageChannel = Field(default=MessageChannel.whatsapp)
    direction: MessageDirection = Field(default=MessageDirection.outbound)
    content: str
    status: MessageStatus = Field(default=MessageStatus.queued)
    provider_reference: str | None = None
    # Loose context for a future AI agent (intent, suggested next action...).
    intent: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: int | None = Field(default=None, primary_key=True)
    actor_user_id: int | None = Field(default=None, foreign_key="users.id")
    action: str
    entity_type: str | None = None
    entity_id: int | None = None
    metadata_json: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
