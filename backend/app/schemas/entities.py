"""Input schemas (create/update) and public-facing read schemas.

Admin read responses return the ORM models directly. Public schemas here
deliberately omit sensitive PII (full address, ID number, internal notes).
"""
from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import (
    AdoptionStatus,
    DocumentType,
    DogGender,
    DogSize,
    DogStatus,
    EntityType,
    LocationType,
    MessageChannel,
    MessageDirection,
    OwnershipTransferStatus,
    SignatureType,
    SurrenderStatus,
    SurrenderType,
    TaskPriority,
    TaskStatus,
    TransferType,
)


# ---------- Person ----------
class PersonCreate(BaseModel):
    first_name: str
    last_name: str | None = None
    phone: str | None = None
    email: str | None = None
    city: str | None = None
    address_private: str | None = None
    id_number_encrypted: str | None = None
    notes: str | None = None


class PersonUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: str | None = None
    city: str | None = None
    address_private: str | None = None
    id_number_encrypted: str | None = None
    notes: str | None = None


# ---------- Dog ----------
class DogCreate(BaseModel):
    name: str | None = None
    breed: str | None = None
    age: float | None = None
    gender: DogGender = DogGender.unknown
    size: DogSize | None = None
    color: str | None = None
    chip_number: str | None = None
    is_neutered: bool | None = None
    is_vaccinated: bool | None = None
    medical_notes: str | None = None
    behavior_notes: str | None = None
    good_with_children: bool | None = None
    good_with_dogs: bool | None = None
    good_with_cats: bool | None = None
    suitable_for_apartment: bool | None = None
    suitable_for_first_time_owner: bool | None = None
    status: DogStatus = DogStatus.draft
    current_location_type: LocationType = LocationType.facility
    current_owner_person_id: int | None = None
    public_description: str | None = None
    internal_notes: str | None = None
    public_area: str | None = None


class DogUpdate(DogCreate):
    gender: DogGender | None = None
    status: DogStatus | None = None
    current_location_type: LocationType | None = None


class DogPublic(BaseModel):
    """Public adoption listing — no internal notes, no chip, no owner id."""
    id: int
    name: str | None
    breed: str | None
    age: float | None
    gender: DogGender
    size: DogSize | None
    color: str | None
    good_with_children: bool | None
    good_with_dogs: bool | None
    good_with_cats: bool | None
    suitable_for_apartment: bool | None
    suitable_for_first_time_owner: bool | None
    public_description: str | None
    public_area: str | None
    current_location_type: LocationType
    status: DogStatus
    photos: list[str] = []


# ---------- Surrender ----------
class SurrenderCreate(BaseModel):
    dog_id: int | None = None
    surrenderer_person_id: int
    surrender_type: SurrenderType = SurrenderType.facility
    start_date: date | None = None
    reason: str | None = None
    privacy_required: bool = False
    allow_direct_contact: bool = False


class SurrenderUpdate(BaseModel):
    dog_id: int | None = None
    surrender_type: SurrenderType | None = None
    reason: str | None = None
    privacy_required: bool | None = None
    allow_direct_contact: bool | None = None
    status: SurrenderStatus | None = None


# ---------- Adoption ----------
class AdoptionLeadCreate(BaseModel):
    person_id: int
    dog_id: int | None = None
    preferred_size: DogSize | None = None
    preferred_breed: str | None = None
    has_children: bool | None = None
    has_other_dogs: bool | None = None
    home_type: str | None = None
    experience_level: str | None = None
    hours_alone: str | None = None
    consent_messages: bool = False
    consent_privacy: bool = False
    source: str | None = None
    notes: str | None = None


class AdoptionCaseCreate(BaseModel):
    dog_id: int
    adopter_person_id: int
    surrender_case_id: int | None = None
    adoption_lead_id: int | None = None
    is_direct_home_adoption: bool = False
    meeting_date: datetime | None = None


# ---------- Ownership transfer ----------
class OwnershipTransferCreate(BaseModel):
    dog_id: int
    from_person_id: int | None = None
    to_person_id: int | None = None
    transfer_type: TransferType
    notes: str | None = None


# ---------- Documents / signatures / tasks / messages ----------
class DocumentCreate(BaseModel):
    related_entity_type: EntityType
    related_entity_id: int
    document_type: DocumentType
    file_url: str | None = None
    uploaded_by_person_id: int | None = None
    is_sensitive: bool = False


class SignatureRequestCreate(BaseModel):
    related_entity_type: EntityType
    related_entity_id: int
    signer_person_id: int
    signature_type: SignatureType


class TaskCreateSchema(BaseModel):
    title: str
    description: str | None = None
    related_entity_type: EntityType | None = None
    related_entity_id: int | None = None
    assigned_to_user_id: int | None = None
    due_date: date | None = None
    priority: TaskPriority = TaskPriority.normal


class TaskUpdateSchema(BaseModel):
    title: str | None = None
    description: str | None = None
    assigned_to_user_id: int | None = None
    due_date: date | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None


class MessageCreate(BaseModel):
    person_id: int
    channel: MessageChannel = MessageChannel.whatsapp
    direction: MessageDirection = MessageDirection.outbound
    content: str
    intent: str | None = None


# ---------- Municipality ----------
class MunicipalityCreate(BaseModel):
    city_name: str
    authority_name: str | None = None
    district: str | None = None
    vet_department_name: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    notes: str | None = None
    is_active: bool = True


class MunicipalityUpdate(MunicipalityCreate):
    city_name: str | None = None


# ---------- Public lead intake ----------
class SurrenderLeadIn(BaseModel):
    # surrenderer
    first_name: str
    last_name: str | None = None
    phone: str
    city: str | None = None
    reason: str | None = None
    surrender_type: SurrenderType = SurrenderType.facility
    privacy_required: bool = False
    allow_direct_contact: bool = False
    consent_privacy: bool = False
    # dog
    dog_name: str | None = None
    dog_breed: str | None = None
    dog_age: float | None = None
    dog_gender: DogGender = DogGender.unknown
    dog_size: DogSize | None = None
    chip_number: str | None = None
    is_neutered: bool | None = None
    is_vaccinated: bool | None = None
    medical_notes: str | None = None
    behavior_notes: str | None = None
    good_with_children: bool | None = None
    good_with_dogs: bool | None = None


class AdoptionLeadIn(BaseModel):
    first_name: str
    last_name: str | None = None
    phone: str
    email: str | None = None
    city: str | None = None
    dog_id: int | None = None
    preferred_size: DogSize | None = None
    preferred_breed: str | None = None
    has_children: bool | None = None
    has_other_dogs: bool | None = None
    home_type: str | None = None
    experience_level: str | None = None
    hours_alone: str | None = None
    consent_messages: bool = False
    consent_privacy: bool = False
    source: str | None = "website"
    notes: str | None = None


class LeadResponse(BaseModel):
    detail: str
    person_id: int
    case_id: int | None = None
    lead_id: int | None = None
