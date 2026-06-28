"""Aggregated case-file response schemas for the back-office CRM screens.

These endpoints are auth-protected, so they may surface admin-level fields
(internal notes, owner ids, PII). They are NEVER used by the public API.
The nested types are the SQLModel table models themselves; `from_attributes`
lets FastAPI serialise ORM instances directly.
"""
from pydantic import BaseModel, ConfigDict

from app.models.adoption import AdoptionCase, AdoptionLead
from app.models.dog import Dog, DogPhoto
from app.models.ownership import OwnershipTransfer
from app.models.person import Person
from app.models.support import Document, Message, SignatureRequest
from app.models.surrender import SurrenderCase


class PersonFile(BaseModel):
    """Full case file for a person: everything related to them in one call."""
    model_config = ConfigDict(from_attributes=True)

    person: Person
    dogs_owned: list[Dog] = []
    surrender_cases: list[SurrenderCase] = []
    adoption_cases: list[AdoptionCase] = []
    adoption_leads: list[AdoptionLead] = []
    documents: list[Document] = []
    recent_messages: list[Message] = []


class DogFile(BaseModel):
    """Full case file for a dog: owner, cases, transfers, documents, photos."""
    model_config = ConfigDict(from_attributes=True)

    dog: Dog
    current_owner: Person | None = None
    surrender_cases: list[SurrenderCase] = []
    adoption_cases: list[AdoptionCase] = []
    adoption_leads: list[AdoptionLead] = []
    ownership_transfers: list[OwnershipTransfer] = []
    documents: list[Document] = []
    photos: list[DogPhoto] = []


class OwnershipTransferDetail(BaseModel):
    """Resolved view of a transfer for the transfer-handling screen."""
    model_config = ConfigDict(from_attributes=True)

    transfer: OwnershipTransfer
    dog: Dog | None = None
    from_person: Person | None = None
    to_person: Person | None = None
    from_authority_name: str | None = None
    to_authority_name: str | None = None
    documents: list[Document] = []
    signature_requests: list[SignatureRequest] = []
    required_documents: list[str] = []
    documents_complete: bool = False
