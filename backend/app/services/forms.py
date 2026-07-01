"""PDF form generation for signed paperwork (forfeit + ownership transfer).

Renders a pre-filled PDF from the case/transfer data, stores it via the storage
adapter as a Document, and kicks off the automation: a SignatureRequest for the
signer plus a follow-up task. Hebrew is shaped right-to-left when a Hebrew-capable
TTF is available (prod installs fonts-dejavu-core); otherwise it falls back to a
Latin core font so a PDF is still produced.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from sqlmodel import Session

from app.adapters.storage import get_storage_provider
from app.core.config import settings
from app.core.logging import logger
from app.models.dog import Dog
from app.models.enums import (
    DocumentStatus,
    DocumentType,
    EntityType,
    SignatureStatus,
    SignatureType,
    TaskPriority,
    TaskStatus,
)
from app.models.ownership import OwnershipTransfer
from app.models.person import Person
from app.models.support import Document, SignatureRequest, Task
from app.models.surrender import SurrenderCase
from app.services import audit


def _person_name(p: Person | None) -> str:
    if not p:
        return "—"
    return " ".join(x for x in [p.first_name, p.last_name] if x) or "—"


def _shape_rtl(text: str) -> str:
    """Reorder a Hebrew/RTL string for correct visual order in the PDF."""
    try:
        from bidi.algorithm import get_display

        return get_display(text)
    except Exception:  # noqa: BLE001 — never let shaping break form generation
        return text


def _render_pdf(title: str, rows: list[tuple[str, str]], note: str) -> bytes:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF(format="A4")
    pdf.add_page()

    font_path = settings.pdf_font_path
    if os.path.isfile(font_path):
        pdf.add_font("Body", "", font_path)
        family, hebrew = "Body", True
    else:
        logger.warning("[FORMS] Hebrew font missing at %s — using Latin fallback", font_path)
        family, hebrew = "Helvetica", False

    def line(text: str, size: int = 12, gap: int = 8) -> None:
        if hebrew:
            shaped = _shape_rtl(text)
        else:
            # Latin core font can't encode Hebrew — keep the PDF valid by
            # dropping unsupported glyphs. (Prod ships the Hebrew font.)
            shaped = text.encode("latin-1", "replace").decode("latin-1")
        pdf.set_font(family, size=size)
        pdf.cell(0, gap, text=shaped, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    line("פנסיון בשדות", size=16, gap=12)
    line(title, size=14, gap=12)
    for label, value in rows:
        line(f"{label}: {value}")
    line("")
    line(note, size=10, gap=6)
    line("")
    line("חתימה: ____________________        תאריך: ____________")

    out = pdf.output()
    return bytes(out)


def _store_and_record(
    session: Session,
    *,
    entity_type: EntityType,
    entity_id: int,
    document_type: DocumentType,
    filename: str,
    data: bytes,
    actor_user_id: int | None,
) -> Document:
    storage = get_storage_provider()
    key = f"{entity_type.value}/{entity_id}/{uuid.uuid4().hex}_{filename}"
    stored = storage.save(key, data)
    doc = Document(
        related_entity_type=entity_type,
        related_entity_id=entity_id,
        document_type=document_type,
        file_url=stored.url,
        uploaded_by_user_id=actor_user_id,
        status=DocumentStatus.uploaded,
        is_sensitive=True,  # generated signable forms are sensitive
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    audit.log(
        session,
        action="document.generate",
        actor_user_id=actor_user_id,
        entity_type=entity_type.value,
        entity_id=entity_id,
        metadata={"document_id": doc.id, "document_type": document_type.value, "file_url": stored.url},
    )
    return doc


def _open_signature_and_task(
    session: Session,
    *,
    entity_type: EntityType,
    entity_id: int,
    signer_person_id: int,
    signature_type: SignatureType,
    task_title: str,
) -> None:
    session.add(
        SignatureRequest(
            related_entity_type=entity_type,
            related_entity_id=entity_id,
            signer_person_id=signer_person_id,
            signature_type=signature_type,
            status=SignatureStatus.pending,
        )
    )
    session.add(
        Task(
            title=task_title,
            related_entity_type=entity_type,
            related_entity_id=entity_id,
            status=TaskStatus.open,
            priority=TaskPriority.high,
        )
    )
    session.commit()


def generate_surrender_form(
    session: Session, case: SurrenderCase, *, actor_user_id: int | None = None
) -> Document:
    """Forfeit form: pre-filled with the owner + dog, signed by the owner. Also
    flags the ID photo as the next thing to collect (via the follow-up task)."""
    owner = session.get(Person, case.surrenderer_person_id)
    dog = session.get(Dog, case.dog_id) if case.dog_id else None
    rows = [
        ("שם המוסר", _person_name(owner)),
        ("טלפון", (owner.phone if owner else None) or "—"),
        ("עיר", (owner.city if owner else None) or "—"),
        ("כלב", (dog.name if dog else None) or "—"),
        ("גזע", (dog.breed if dog else None) or "—"),
        ("שבב", (dog.chip_number if dog else None) or "—"),
        ("סוג מסירה", case.surrender_type.value),
    ]
    note = "אני החתום מטה מוסר את הכלב הנ\"ל לפנסיון בשדות מרצוני החופשי. יש לצרף צילום תעודת זהות."
    data = _render_pdf("טופס מסירת כלב", rows, note)
    doc = _store_and_record(
        session,
        entity_type=EntityType.surrender_case,
        entity_id=case.id,
        document_type=DocumentType.surrender_form,
        filename="surrender_form.pdf",
        data=data,
        actor_user_id=actor_user_id,
    )
    if case.surrenderer_person_id:
        _open_signature_and_task(
            session,
            entity_type=EntityType.surrender_case,
            entity_id=case.id,
            signer_person_id=case.surrenderer_person_id,
            signature_type=SignatureType.surrenderer,
            task_title=f"החתמת טופס מסירה + צילום ת\"ז — תיק מסירה #{case.id}",
        )
    return doc


def generate_transfer_form(
    session: Session, transfer: OwnershipTransfer, *, actor_user_id: int | None = None
) -> Document:
    """Ownership-transfer form, signed by the surrenderer (from_person)."""
    from_p = session.get(Person, transfer.from_person_id) if transfer.from_person_id else None
    to_p = session.get(Person, transfer.to_person_id) if transfer.to_person_id else None
    dog = session.get(Dog, transfer.dog_id) if transfer.dog_id else None
    rows = [
        ("מוסר", _person_name(from_p)),
        ("מקבל", _person_name(to_p) if to_p else "פנסיון בשדות"),
        ("כלב", (dog.name if dog else None) or "—"),
        ("שבב", (dog.chip_number if dog else None) or "—"),
        ("סוג העברה", transfer.transfer_type.value),
    ]
    note = "טופס העברת בעלות על כלב. יש לצרף צילומי ת\"ז של הצדדים ותמונת הבעלים החדש עם הכלב."
    data = _render_pdf("טופס העברת בעלות", rows, note)
    doc = _store_and_record(
        session,
        entity_type=EntityType.ownership_transfer,
        entity_id=transfer.id,
        document_type=DocumentType.ownership_transfer_form,
        filename="ownership_transfer_form.pdf",
        data=data,
        actor_user_id=actor_user_id,
    )
    if transfer.from_person_id:
        _open_signature_and_task(
            session,
            entity_type=EntityType.ownership_transfer,
            entity_id=transfer.id,
            signer_person_id=transfer.from_person_id,
            signature_type=SignatureType.surrenderer,
            task_title=f"החתמת טופס העברת בעלות — העברה #{transfer.id}",
        )
    return doc
