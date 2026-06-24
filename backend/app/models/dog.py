from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.base import utcnow
from app.models.enums import DogGender, DogSize, DogStatus, LocationType


class Dog(SQLModel, table=True):
    __tablename__ = "dogs"

    id: int | None = Field(default=None, primary_key=True)
    name: str | None = None
    breed: str | None = None
    age: float | None = None  # years
    gender: DogGender = Field(default=DogGender.unknown)
    size: DogSize | None = None
    color: str | None = None
    chip_number: str | None = Field(default=None, index=True)
    is_neutered: bool | None = None
    is_vaccinated: bool | None = None
    medical_notes: str | None = None
    behavior_notes: str | None = None
    good_with_children: bool | None = None
    good_with_dogs: bool | None = None
    good_with_cats: bool | None = None
    suitable_for_apartment: bool | None = None
    suitable_for_first_time_owner: bool | None = None

    status: DogStatus = Field(default=DogStatus.draft, index=True)
    current_location_type: LocationType = Field(default=LocationType.facility)
    current_owner_person_id: int | None = Field(default=None, foreign_key="people.id")

    # Public marketing copy vs internal notes.
    public_description: str | None = None
    internal_notes: str | None = None
    # General area shown publicly (city/region) when dog stays at owner's home.
    public_area: str | None = None

    created_at: datetime = Field(default_factory=utcnow)


class DogPhoto(SQLModel, table=True):
    __tablename__ = "dog_photos"

    id: int | None = Field(default=None, primary_key=True)
    dog_id: int = Field(foreign_key="dogs.id", index=True)
    file_url: str
    is_primary: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utcnow)
