from pydantic import BaseModel

from app.models.enums import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None = None
    role: UserRole
    is_active: bool


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    phone: str | None = None
    role: UserRole = UserRole.field_worker
