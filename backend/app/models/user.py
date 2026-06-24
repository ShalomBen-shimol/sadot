from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.base import utcnow
from app.models.enums import UserRole


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    phone: str | None = None
    role: UserRole = Field(default=UserRole.field_worker)
    password_hash: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utcnow)
