from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.base import utcnow


class Person(SQLModel, table=True):
    """A surrenderer, adopter or other contact. Holds sensitive PII."""
    __tablename__ = "people"

    id: int | None = Field(default=None, primary_key=True)
    first_name: str
    last_name: str | None = None
    phone: str | None = Field(default=None, index=True)
    email: str | None = None
    city: str | None = Field(default=None, index=True)
    # Private full address — never exposed on public endpoints.
    address_private: str | None = None
    # National ID — stored encrypted-at-rest in production; sensitive.
    id_number_encrypted: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
