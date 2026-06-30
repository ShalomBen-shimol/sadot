"""Outbound notifications: persists a Message row and dispatches via adapter."""
from sqlmodel import Session

from app.adapters import get_email_provider, get_messaging_provider
from app.models.enums import MessageChannel, MessageDirection, MessageStatus
from app.models.person import Person
from app.models.support import Message


def send_whatsapp(session: Session, person: Person, content: str, intent: str | None = None) -> Message:
    provider = get_messaging_provider()
    msg = Message(
        person_id=person.id,
        channel=MessageChannel.whatsapp,
        direction=MessageDirection.outbound,
        content=content,
        intent=intent,
        status=MessageStatus.queued,
    )
    if person.phone:
        result = provider.send(person.phone, content)
        msg.provider_reference = result.provider_reference
        msg.status = MessageStatus.sent if result.status == "sent" else MessageStatus.failed
    else:
        msg.status = MessageStatus.failed
    session.add(msg)
    session.commit()
    session.refresh(msg)
    return msg


def send_email(
    to: str,
    subject: str,
    body: str,
    attachments: list[str] | None = None,
    session: Session | None = None,
) -> str:
    # Pass the request session so provider selection reads the same DB the
    # admin configured (in production it's the global engine either way).
    provider = get_email_provider(session)
    result = provider.send(to, subject, body, attachments)
    return result.provider_reference
