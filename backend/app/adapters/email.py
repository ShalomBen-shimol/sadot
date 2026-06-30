"""Email abstraction.

Resolution order in get_email_provider():
  1. The admin-configured SMTP account (email_settings row, enabled) — Gmail
     app-password sending set up from the UI.
  2. Env-configured SMTP (settings.smtp_host) — fallback / non-UI deploys.
  3. Mock — logs only (dev / not configured).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.message import EmailMessage
import mimetypes
import os
import smtplib

from app.core.config import settings
from app.core.logging import logger


@dataclass
class EmailResult:
    provider_reference: str
    status: str


class EmailProvider(ABC):
    name: str

    @abstractmethod
    def send(self, to: str, subject: str, body: str, attachments: list[str] | None = None) -> EmailResult: ...


class MockEmailProvider(EmailProvider):
    name = "mock"

    def send(self, to: str, subject: str, body: str, attachments: list[str] | None = None) -> EmailResult:
        att = f" (+{len(attachments)} attachments)" if attachments else ""
        logger.info("[MOCK EMAIL] -> %s | %s%s", to, subject, att)
        return EmailResult(provider_reference=f"mock-email-{abs(hash((to, subject))) % 10**8}", status="sent")


class SmtpEmailProvider(EmailProvider):
    """Sends over SMTP+STARTTLS. With Gmail, ``username`` is the address and
    ``password`` is a 16-char App Password (requires 2FA on the account)."""

    name = "smtp"

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str | None = None,
        from_name: str | None = None,
        use_tls: bool = True,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email or username
        self.from_name = from_name
        self.use_tls = use_tls

    def _build(self, to: str, subject: str, body: str, attachments: list[str] | None) -> EmailMessage:
        msg = EmailMessage()
        msg["From"] = f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        for path in attachments or []:
            if not os.path.isfile(path):
                logger.warning("[SMTP] attachment missing, skipping: %s", path)
                continue
            ctype, _ = mimetypes.guess_type(path)
            maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
            with open(path, "rb") as fh:
                msg.add_attachment(
                    fh.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(path)
                )
        return msg

    def send(self, to: str, subject: str, body: str, attachments: list[str] | None = None) -> EmailResult:
        msg = self._build(to, subject, body, attachments)
        try:
            with smtplib.SMTP(self.host, self.port, timeout=30) as smtp:
                smtp.ehlo()
                if self.use_tls:
                    smtp.starttls()
                    smtp.ehlo()
                smtp.login(self.username, self.password)
                smtp.send_message(msg)
            logger.info("[SMTP] sent -> %s | %s", to, subject)
            return EmailResult(provider_reference=msg.get("Message-Id", "smtp-sent"), status="sent")
        except Exception as exc:  # noqa: BLE001 — surface any SMTP failure to the caller
            logger.error("[SMTP] send failed -> %s: %s", to, exc)
            return EmailResult(provider_reference=f"smtp-error: {exc}", status="failed")


def _provider_from_settings_row(session=None) -> SmtpEmailProvider | None:
    """Load the admin-configured SMTP account from the DB, if enabled. Reuses
    ``session`` when given (request/test scope); otherwise opens one on the
    global engine (production)."""
    # Imported here to avoid a circular import at module load (adapters <- db).
    from sqlmodel import Session

    from app.core.crypto import decrypt
    from app.core.database import engine
    from app.models.settings import EmailSettings

    try:
        if session is not None:
            cfg = session.get(EmailSettings, 1)
        else:
            with Session(engine) as own:
                cfg = own.get(EmailSettings, 1)
    except Exception as exc:  # noqa: BLE001 — never let config lookup break sending
        logger.warning("[EMAIL] could not load email_settings: %s", exc)
        return None

    if not cfg or not cfg.enabled or not cfg.username or not cfg.password_encrypted:
        return None
    password = decrypt(cfg.password_encrypted)
    if not password:
        logger.warning("[EMAIL] stored password could not be decrypted (SECRET_KEY changed?)")
        return None
    return SmtpEmailProvider(
        host=cfg.host,
        port=cfg.port,
        username=cfg.username,
        password=password,
        from_email=cfg.from_email or cfg.username,
        from_name=cfg.from_name,
        use_tls=cfg.use_tls,
    )


def get_email_provider(session=None) -> EmailProvider:
    provider = _provider_from_settings_row(session)
    if provider is not None:
        return provider
    if settings.smtp_host and settings.smtp_user and settings.smtp_password:
        return SmtpEmailProvider(
            host=settings.smtp_host,
            port=int(settings.smtp_port or 587),
            username=settings.smtp_user,
            password=settings.smtp_password,
            use_tls=True,
        )
    return MockEmailProvider()
