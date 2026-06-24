from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.base import utcnow
from app.models.enums import AdoptionLeadStatus, AdoptionStatus, DogSize


class AdoptionLead(SQLModel, table=True):
    __tablename__ = "adoption_leads"

    id: int | None = Field(default=None, primary_key=True)
    person_id: int = Field(foreign_key="people.id", index=True)
    dog_id: int | None = Field(default=None, foreign_key="dogs.id")
    preferred_size: DogSize | None = None
    preferred_breed: str | None = None
    has_children: bool | None = None
    has_other_dogs: bool | None = None
    home_type: str | None = None  # apartment / house / ...
    experience_level: str | None = None  # none / some / experienced
    hours_alone: str | None = None
    consent_messages: bool = Field(default=False)
    consent_privacy: bool = Field(default=False)
    status: AdoptionLeadStatus = Field(default=AdoptionLeadStatus.new, index=True)
    source: str | None = None  # website / qr / whatsapp / monday
    notes: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class AdoptionCase(SQLModel, table=True):
    __tablename__ = "adoption_cases"

    id: int | None = Field(default=None, primary_key=True)
    dog_id: int = Field(foreign_key="dogs.id", index=True)
    adopter_person_id: int = Field(foreign_key="people.id", index=True)
    surrender_case_id: int | None = Field(default=None, foreign_key="surrender_cases.id")
    adoption_lead_id: int | None = Field(default=None, foreign_key="adoption_leads.id")
    status: AdoptionStatus = Field(default=AdoptionStatus.new_lead, index=True)
    meeting_date: datetime | None = None
    # True when dog is handed directly from surrenderer's home to adopter.
    is_direct_home_adoption: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utcnow)
