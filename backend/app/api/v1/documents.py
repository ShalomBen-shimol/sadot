"""Documents API: multipart upload via the storage adapter + listing.

Replaces the generic CRUD router for documents so uploads always go through the
storage abstraction and are recorded in the audit log. Sensitive documents
(ID photos, signed forms) are flagged so downstream access stays gated.
"""
import re
import uuid

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from app.adapters.storage import get_storage_provider
from app.api.deps import CurrentUser, SessionDep
from app.models.enums import DocumentStatus, DocumentType, EntityType
from app.models.support import Document
from app.repositories.base import CRUDRepository
from app.services import audit

router = APIRouter(prefix="/documents", tags=["documents"])
repo = CRUDRepository(Document)

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_filename(name: str | None) -> str:
    """Reduce an uploaded filename to a safe, path-component-free token."""
    base = (name or "file").rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    cleaned = _SAFE_NAME.sub("_", base).strip("._")
    return cleaned or "file"


@router.get("", response_model=list[Document])
def list_documents(
    session: SessionDep,
    _: CurrentUser,
    entity_type: EntityType | None = None,
    entity_id: int | None = None,
    document_type: DocumentType | None = None,
    document_status: DocumentStatus | None = Query(default=None, alias="status"),
    is_sensitive: bool | None = None,
    offset: int = 0,
    limit: int = Query(default=100, le=500),
):
    """List documents, optionally filtered by related entity, type, status, or
    sensitivity. Powers both the per-case managers and the central documents
    console (which filters across all entities)."""
    return repo.list(
        session,
        offset=offset,
        limit=limit,
        filters={
            "related_entity_type": entity_type,
            "related_entity_id": entity_id,
            "document_type": document_type,
            "status": document_status,
            "is_sensitive": is_sensitive,
        },
    )


@router.get("/{document_id}", response_model=Document)
def get_document(document_id: int, session: SessionDep, _: CurrentUser):
    doc = repo.get(session, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


def _set_status(
    document_id: int, new_status: DocumentStatus, session: SessionDep, user: CurrentUser
) -> Document:
    doc = repo.get(session, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    doc.status = new_status
    session.add(doc)
    session.commit()
    session.refresh(doc)
    audit.log(
        session,
        action=f"document.{new_status.value}",
        actor_user_id=user.id,
        entity_type=doc.related_entity_type.value,
        entity_id=doc.related_entity_id,
        metadata={"document_id": doc.id, "document_type": doc.document_type.value},
    )
    return doc


@router.post("/{document_id}/approve", response_model=Document)
def approve_document(document_id: int, session: SessionDep, user: CurrentUser):
    return _set_status(document_id, DocumentStatus.approved, session, user)


@router.post("/{document_id}/reject", response_model=Document)
def reject_document(document_id: int, session: SessionDep, user: CurrentUser):
    return _set_status(document_id, DocumentStatus.rejected, session, user)


@router.post("/upload", response_model=Document, status_code=status.HTTP_201_CREATED)
async def upload_document(
    session: SessionDep,
    user: CurrentUser,
    file: UploadFile = File(...),
    related_entity_type: EntityType = Form(...),
    related_entity_id: int = Form(...),
    document_type: DocumentType = Form(...),
    is_sensitive: bool = Form(False),
):
    """Store an uploaded file via the storage adapter and record a Document row."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Empty file")

    storage = get_storage_provider()
    key = (
        f"{related_entity_type.value}/{related_entity_id}/"
        f"{uuid.uuid4().hex}_{_safe_filename(file.filename)}"
    )
    stored = storage.save(key, data)

    doc = repo.create(
        session,
        {
            "related_entity_type": related_entity_type,
            "related_entity_id": related_entity_id,
            "document_type": document_type,
            "file_url": stored.url,
            "uploaded_by_user_id": user.id,
            "status": DocumentStatus.uploaded,
            "is_sensitive": is_sensitive,
        },
    )

    audit.log(
        session,
        action="document.upload",
        actor_user_id=user.id,
        entity_type=related_entity_type.value,
        entity_id=related_entity_id,
        metadata={
            "document_id": doc.id,
            "document_type": document_type.value,
            "is_sensitive": is_sensitive,
            "file_url": stored.url,
            "original_filename": file.filename,
        },
    )
    return doc
