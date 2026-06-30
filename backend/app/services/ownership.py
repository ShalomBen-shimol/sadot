"""Ownership-transfer workflow + authority follow-up mechanism.

Sending an email to the authority is NOT enough: every submission opens an
automatic follow-up task and schedules the next follow-up. Follow-ups keep
recurring until the authority confirms or the process is stopped manually.
"""
from datetime import date, datetime, timedelta, timezone

from sqlmodel import Session, select

from app.core.config import settings
from app.models.dog import Dog
from app.models.enums import (
    DocumentType,
    DogStatus,
    EntityType,
    LocationType,
    OwnershipTransferStatus,
    TaskPriority,
    TransferType,
)
from app.models.municipality import Municipality
from app.models.ownership import OwnershipTransfer
from app.models.support import Document, Task
from app.services import audit
from app.services.municipality import resolve_by_city
from app.services.notifications import send_email


def create_transfer(
    session: Session,
    data: dict,
    *,
    from_city: str | None = None,
    to_city: str | None = None,
) -> OwnershipTransfer:
    transfer = OwnershipTransfer(**data)
    from_auth = resolve_by_city(session, from_city)
    to_auth = resolve_by_city(session, to_city)
    transfer.from_authority_id = from_auth.id if from_auth else None
    transfer.to_authority_id = to_auth.id if to_auth else None
    transfer.status = OwnershipTransferStatus.waiting_for_documents
    session.add(transfer)
    session.commit()
    session.refresh(transfer)
    return transfer


def required_documents(transfer: OwnershipTransfer) -> list[DocumentType]:
    docs = [
        DocumentType.ownership_transfer_form,
        DocumentType.id_card_surrenderer,
    ]
    if transfer.transfer_type != TransferType.surrender_to_facility:
        # Transfer between two individuals: receiver's approval + ID, plus the
        # for-the-record photo of the new owner with the dog.
        docs += [
            DocumentType.receiver_approval_form,
            DocumentType.id_card_receiver,
            DocumentType.adopter_with_dog_photo,
        ]
    return docs


def has_all_documents(session: Session, transfer: OwnershipTransfer) -> bool:
    present = {
        d.document_type
        for d in session.exec(
            select(Document).where(
                Document.related_entity_type == EntityType.ownership_transfer,
                Document.related_entity_id == transfer.id,
            )
        ).all()
    }
    return all(req in present for req in required_documents(transfer))


def mark_ready_to_send(session: Session, transfer: OwnershipTransfer) -> OwnershipTransfer:
    transfer.status = OwnershipTransferStatus.ready_to_send
    session.add(transfer)
    session.commit()
    session.refresh(transfer)
    return transfer


def send_to_authority(
    session: Session, transfer: OwnershipTransfer, actor_user_id: int | None = None
) -> OwnershipTransfer:
    """Email the relevant authority and open the first follow-up task."""
    now = datetime.now(timezone.utc)
    # The destination authority is the receiver's authority; for a surrender to
    # the facility it is the facility's authority (to_authority), otherwise the
    # receiver's. We notify both where known.
    recipients = [m for m in (transfer.to_authority_id, transfer.from_authority_id) if m]
    for auth_id in recipients:
        authority = session.get(Municipality, auth_id)
        if authority and authority.email:
            send_email(
                to=authority.email,
                subject=f"בקשת העברת בעלות על כלב — תיק #{transfer.id}",
                body="מצורפים מסמכי העברת הבעלות. נא לאשר קליטה ועדכון במאגר השבבים.",
                session=session,
            )

    transfer.sent_to_authority_at = now
    transfer.last_followup_at = now
    transfer.next_followup_at = now + timedelta(days=settings.followup_days)
    transfer.status = OwnershipTransferStatus.sent_to_authority
    session.add(transfer)
    session.commit()
    session.refresh(transfer)

    _create_followup_task(session, transfer, first=True)
    audit.log(
        session,
        action="ownership_transfer.sent_to_authority",
        actor_user_id=actor_user_id,
        entity_type="ownership_transfer",
        entity_id=transfer.id,
    )
    return transfer


def _create_followup_task(session: Session, transfer: OwnershipTransfer, first: bool = False) -> Task:
    title = (
        f"מעקב אישור רשות — העברת בעלות #{transfer.id}"
        if first
        else f"תזכורת מעקב רשות — העברת בעלות #{transfer.id}"
    )
    task = Task(
        title=title,
        description="ודא שהרשות קלטה את הבקשה וביצעה את העברת הבעלות במאגר. אם אין אישור — שלח תזכורת.",
        related_entity_type=EntityType.ownership_transfer,
        related_entity_id=transfer.id,
        due_date=transfer.next_followup_at.date() if transfer.next_followup_at else date.today(),
        priority=TaskPriority.high,
        is_followup=True,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def confirm(session: Session, transfer: OwnershipTransfer, actor_user_id: int | None = None) -> OwnershipTransfer:
    """Authority confirmed the transfer; update dog status accordingly."""
    transfer.status = OwnershipTransferStatus.confirmed
    transfer.confirmed_at = datetime.now(timezone.utc)
    transfer.next_followup_at = None
    session.add(transfer)
    session.commit()

    dog = session.get(Dog, transfer.dog_id)
    if dog:
        if transfer.transfer_type == TransferType.surrender_to_facility:
            dog.status = DogStatus.in_facility
            dog.current_location_type = LocationType.facility
            dog.current_owner_person_id = None  # facility-owned
        else:
            dog.status = DogStatus.adopted
            dog.current_location_type = LocationType.adopted
            dog.current_owner_person_id = transfer.to_person_id
        session.add(dog)
        session.commit()

    audit.log(
        session,
        action="ownership_transfer.confirmed",
        actor_user_id=actor_user_id,
        entity_type="ownership_transfer",
        entity_id=transfer.id,
    )
    session.refresh(transfer)
    return transfer


def stop_manually(session: Session, transfer: OwnershipTransfer, actor_user_id: int | None = None) -> OwnershipTransfer:
    transfer.status = OwnershipTransferStatus.stopped_manually
    transfer.next_followup_at = None
    session.add(transfer)
    session.commit()
    session.refresh(transfer)
    audit.log(
        session,
        action="ownership_transfer.stopped_manually",
        actor_user_id=actor_user_id,
        entity_type="ownership_transfer",
        entity_id=transfer.id,
    )
    return transfer


def run_due_followups(session: Session) -> int:
    """Find transfers awaiting authority confirmation whose follow-up is due,
    raise a reminder task and reschedule the next follow-up. Returns count."""
    now = datetime.now(timezone.utc)
    due = session.exec(
        select(OwnershipTransfer).where(
            OwnershipTransfer.status.in_(  # type: ignore[attr-defined]
                [
                    OwnershipTransferStatus.sent_to_authority,
                    OwnershipTransferStatus.followup_required,
                ]
            ),
            OwnershipTransfer.next_followup_at != None,  # noqa: E711
            OwnershipTransfer.next_followup_at <= now,
        )
    ).all()

    for transfer in due:
        transfer.status = OwnershipTransferStatus.followup_required
        transfer.last_followup_at = now
        transfer.next_followup_at = now + timedelta(days=settings.followup_days)
        session.add(transfer)
        session.commit()
        _create_followup_task(session, transfer)
        audit.log(
            session,
            action="ownership_transfer.followup_reminder",
            entity_type="ownership_transfer",
            entity_id=transfer.id,
        )
    return len(due)
