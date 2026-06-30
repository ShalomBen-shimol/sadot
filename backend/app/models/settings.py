"""Editable runtime settings configured from the admin UI (not env vars).

Currently just the outbound-email account. Single-row table (id=1)."""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EmailSettings(SQLModel, table=True):
    """SMTP sending account for authority emails. The password is stored
    encrypted (see app.core.crypto); it is never returned by the API."""
    __tablename__ = "email_settings"

    id: int | None = Field(default=None, primary_key=True)
    provider: str = "smtp"                 # room for gmail_oauth / workspace_sa later
    host: str = "smtp.gmail.com"
    port: int = 587
    use_tls: bool = True
    username: str | None = None            # the Gmail address (login + default From)
    password_encrypted: str | None = None  # Fernet ciphertext of the app password
    from_name: str | None = None           # display name, e.g. "פנסיון בשדות"
    from_email: str | None = None          # defaults to username when empty
    enabled: bool = False                  # must be on for real sending
    updated_at: datetime = Field(default_factory=_utcnow)
