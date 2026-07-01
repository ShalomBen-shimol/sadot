"""Configurable ownership-transfer workflow engine.

An active TransferWorkflow per transfer_type is an ordered list of steps. The
engine walks them: **gate** steps (documents / signatures / await_confirmation)
block until satisfied; **action** steps (email / task / update_dog) run their
side-effect on entry. Action steps may be `manual` so the owner triggers them
(e.g. sending to the authority) rather than firing automatically.

Seeded defaults reproduce the previous hardcoded flow, so behavior is unchanged
until the owner edits a workflow.
"""
from datetime import date, datetime, timedelta, timezone

from sqlmodel import Session, select

from app.core.config import settings
from app.core.logging import logger
from app.models.dog import Dog
from app.models.enums import (
    DocumentStatus,
    DogStatus,
    EntityType,
    OwnershipTransferStatus,
    SignatureStatus,
    TaskPriority,
    TaskStatus,
    TransferType,
)
from app.models.municipality import Municipality
from app.models.ownership import OwnershipTransfer
from app.models.person import Person
from app.models.support import Document, SignatureRequest, Task
from app.models.workflow import TransferWorkflow
from app.services import audit
from app.services.notifications import send_email

ACTION_TYPES = {"email", "task", "update_dog"}
GATE_TYPES = {"documents", "signatures", "await_confirmation"}

# Vocabulary surfaced to the admin builder so it can render field editors.
STEP_TYPES = [
    {
        "type": "documents",
        "label": "איסוף מסמכים",
        "kind": "gate",
        "fields": [{"name": "documents", "type": "documenttypes", "label": "מסמכים נדרשים"}],
    },
    {
        "type": "signatures",
        "label": "חתימות",
        "kind": "gate",
        "fields": [{"name": "signers", "type": "signaturetypes", "label": "חותמים נדרשים"}],
    },
    {
        "type": "email",
        "label": "שליחת מייל",
        "kind": "action",
        "manual_default": True,
        "fields": [
            {
                "name": "recipient",
                "type": "select",
                "label": "נמען",
                "options": ["authority_to", "authority_from", "from_person", "to_person"],
            },
            {"name": "subject", "type": "text", "label": "נושא"},
            {"name": "body", "type": "textarea", "label": "תוכן"},
        ],
    },
    {
        "type": "task",
        "label": "יצירת משימה",
        "kind": "action",
        "fields": [
            {"name": "title", "type": "text", "label": "כותרת"},
            {
                "name": "priority",
                "type": "select",
                "label": "עדיפות",
                "options": ["low", "normal", "high", "urgent"],
            },
        ],
    },
    {
        "type": "await_confirmation",
        "label": "המתנה לאישור הרשות",
        "kind": "gate",
        "fields": [{"name": "followup_days", "type": "number", "label": "תזכורת כל (ימים)"}],
    },
    {
        "type": "update_dog",
        "label": "עדכון סטטוס כלב",
        "kind": "action",
        "fields": [
            {
                "name": "status",
                "type": "select",
                "label": "סטטוס",
                "options": [s.value for s in DogStatus],
            },
            {"name": "owner", "type": "select", "label": "בעלים", "options": ["to_person", "none"]},
        ],
    },
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _email_step() -> dict:
    return {
        "type": "email",
        "title": "שליחה לרשות",
        "manual": True,
        "config": {
            "recipient": "authority_to",
            "subject": "בקשת העברת בעלות על כלב",
            "body": "מצורפים מסמכי העברת הבעלות. נא לאשר קליטה ועדכון במאגר השבבים.",
        },
    }


def _await_step() -> dict:
    return {
        "type": "await_confirmation",
        "title": "המתנה לאישור הרשות",
        "config": {"followup_days": settings.followup_days},
    }


# Parity with the previous hardcoded flow.
DEFAULT_WORKFLOWS: dict[str, list[dict]] = {
    TransferType.surrender_to_facility.value: [
        {
            "type": "documents",
            "title": "איסוף מסמכים",
            "config": {"documents": ["ownership_transfer_form", "id_card_surrenderer"]},
        },
        _email_step(),
        _await_step(),
    ],
    TransferType.facility_to_adopter.value: [
        {
            "type": "documents",
            "title": "איסוף מסמכים",
            "config": {
                "documents": [
                    "ownership_transfer_form",
                    "id_card_surrenderer",
                    "receiver_approval_form",
                    "id_card_receiver",
                    "adopter_with_dog_photo",
                ]
            },
        },
        _email_step(),
        _await_step(),
    ],
}
DEFAULT_WORKFLOWS[TransferType.direct_surrenderer_to_adopter.value] = DEFAULT_WORKFLOWS[
    TransferType.facility_to_adopter.value
]


def seed_workflows(session: Session) -> None:
    for ttype, steps in DEFAULT_WORKFLOWS.items():
        exists = session.exec(
            select(TransferWorkflow).where(TransferWorkflow.transfer_type == ttype)
        ).first()
        if not exists:
            session.add(
                TransferWorkflow(transfer_type=ttype, version=1, is_active=True, steps=steps)
            )
    session.commit()


def get_active_workflow(session: Session, transfer_type: TransferType | str) -> TransferWorkflow:
    ttype = transfer_type.value if isinstance(transfer_type, TransferType) else transfer_type
    wf = session.exec(
        select(TransferWorkflow)
        .where(TransferWorkflow.transfer_type == ttype, TransferWorkflow.is_active == True)  # noqa: E712
    ).first()
    if wf:
        return wf
    return TransferWorkflow(transfer_type=ttype, steps=DEFAULT_WORKFLOWS.get(ttype, []))


# ---------------- gates ----------------
def _present_doc_types(session: Session, transfer: OwnershipTransfer) -> set[str]:
    return {
        d.document_type.value
        for d in session.exec(
            select(Document).where(
                Document.related_entity_type == EntityType.ownership_transfer,
                Document.related_entity_id == transfer.id,
                Document.status.in_([DocumentStatus.uploaded, DocumentStatus.approved]),  # type: ignore[attr-defined]
            )
        ).all()
    }


def _signed_types(session: Session, transfer: OwnershipTransfer) -> set[str]:
    return {
        s.signature_type.value
        for s in session.exec(
            select(SignatureRequest).where(
                SignatureRequest.related_entity_type == EntityType.ownership_transfer,
                SignatureRequest.related_entity_id == transfer.id,
                SignatureRequest.status == SignatureStatus.signed,
            )
        ).all()
    }


def gate_satisfied(session: Session, transfer: OwnershipTransfer, step: dict) -> bool:
    stype = step.get("type")
    cfg = step.get("config", {})
    if stype == "documents":
        required = set(cfg.get("documents", []))
        return required.issubset(_present_doc_types(session, transfer))
    if stype == "signatures":
        required = set(cfg.get("signers", []))
        return required.issubset(_signed_types(session, transfer))
    if stype == "await_confirmation":
        return transfer.confirmed_at is not None
    return True


def blocking_reason(session: Session, transfer: OwnershipTransfer, step: dict) -> str | None:
    stype = step.get("type")
    cfg = step.get("config", {})
    if stype == "documents":
        missing = set(cfg.get("documents", [])) - _present_doc_types(session, transfer)
        return "חסרים מסמכים: " + ", ".join(sorted(missing)) if missing else None
    if stype == "signatures":
        missing = set(cfg.get("signers", [])) - _signed_types(session, transfer)
        return "חסרות חתימות: " + ", ".join(sorted(missing)) if missing else None
    if stype == "await_confirmation":
        return "ממתין לאישור הרשות" if transfer.confirmed_at is None else None
    return None


# ---------------- actions ----------------
def _recipient_emails(session: Session, transfer: OwnershipTransfer, recipient: str) -> list[str]:
    def auth_email(auth_id: int | None) -> str | None:
        m = session.get(Municipality, auth_id) if auth_id else None
        return m.email if m else None

    def person_email(pid: int | None) -> str | None:
        p = session.get(Person, pid) if pid else None
        return p.email if p else None

    mapping = {
        "authority_to": auth_email(transfer.to_authority_id),
        "authority_from": auth_email(transfer.from_authority_id),
        "from_person": person_email(transfer.from_person_id),
        "to_person": person_email(transfer.to_person_id),
    }
    val = mapping.get(recipient)
    return [val] if val else []


def _do_email(session: Session, transfer: OwnershipTransfer, step: dict) -> None:
    cfg = step.get("config", {})
    recipient = cfg.get("recipient", "authority_to")
    for to in _recipient_emails(session, transfer, recipient):
        send_email(to=to, subject=cfg.get("subject", ""), body=cfg.get("body", ""), session=session)
    now = _utcnow()
    transfer.sent_to_authority_at = now
    transfer.last_followup_at = now
    transfer.next_followup_at = now + timedelta(days=int(cfg.get("followup_days", settings.followup_days)))
    transfer.status = OwnershipTransferStatus.sent_to_authority
    session.add(transfer)
    if recipient.startswith("authority"):
        session.add(
            Task(
                title=f"מעקב אישור רשות — העברת בעלות #{transfer.id}",
                related_entity_type=EntityType.ownership_transfer,
                related_entity_id=transfer.id,
                due_date=transfer.next_followup_at.date(),
                priority=TaskPriority.high,
                is_followup=True,
            )
        )
    session.commit()


def _do_task(session: Session, transfer: OwnershipTransfer, step: dict) -> None:
    cfg = step.get("config", {})
    try:
        priority = TaskPriority(cfg.get("priority", "normal"))
    except ValueError:
        priority = TaskPriority.normal
    session.add(
        Task(
            title=cfg.get("title") or f"משימה — העברה #{transfer.id}",
            related_entity_type=EntityType.ownership_transfer,
            related_entity_id=transfer.id,
            status=TaskStatus.open,
            priority=priority,
        )
    )
    session.commit()


def _do_update_dog(session: Session, transfer: OwnershipTransfer, step: dict) -> None:
    cfg = step.get("config", {})
    dog = session.get(Dog, transfer.dog_id) if transfer.dog_id else None
    if not dog:
        return
    try:
        dog.status = DogStatus(cfg.get("status", dog.status.value))
    except ValueError:
        pass
    owner = cfg.get("owner")
    if owner == "to_person":
        dog.current_owner_person_id = transfer.to_person_id
    elif owner == "none":
        dog.current_owner_person_id = None
    session.add(dog)
    session.commit()


def _execute_action(session: Session, transfer: OwnershipTransfer, step: dict) -> None:
    stype = step.get("type")
    if stype == "email":
        _do_email(session, transfer, step)
    elif stype == "task":
        _do_task(session, transfer, step)
    elif stype == "update_dog":
        _do_update_dog(session, transfer, step)


# ---------------- engine ----------------
def advance(
    session: Session, transfer: OwnershipTransfer, *, run_current_action: bool = False
) -> dict:
    """Walk the workflow from the transfer's current step: auto-pass satisfied
    gates and non-manual actions; stop at the first blocked gate or a manual
    action awaiting the owner. `run_current_action` fires the current manual
    action once (the owner clicked its button)."""
    wf = get_active_workflow(session, transfer.transfer_type)
    steps = wf.steps or []
    idx = transfer.workflow_step or 0

    for _ in range(200):  # guard against a malformed loop
        if idx >= len(steps):
            break
        step = steps[idx]
        stype = step.get("type")
        if stype in ACTION_TYPES:
            if step.get("manual") and not run_current_action:
                break
            _execute_action(session, transfer, step)
            run_current_action = False
            idx += 1
            transfer.workflow_step = idx
            session.add(transfer)
            session.commit()
            continue
        # gate
        if gate_satisfied(session, transfer, step):
            idx += 1
            transfer.workflow_step = idx
            session.add(transfer)
            session.commit()
            continue
        break

    session.refresh(transfer)
    return status(session, transfer)


def status(session: Session, transfer: OwnershipTransfer) -> dict:
    wf = get_active_workflow(session, transfer.transfer_type)
    steps = wf.steps or []
    idx = transfer.workflow_step or 0
    done = idx >= len(steps)
    current = None if done else steps[idx]
    blocking = None
    awaiting_action = False
    if current:
        if current.get("type") in GATE_TYPES:
            blocking = blocking_reason(session, transfer, current)
        elif current.get("type") in ACTION_TYPES and current.get("manual"):
            awaiting_action = True
    return {
        "step_index": idx,
        "total": len(steps),
        "current": current,
        "done": done,
        "blocking": blocking,
        "awaiting_action": awaiting_action,
        "steps": steps,
    }
