"""Admin-only integration settings (outbound email account)."""
from datetime import datetime, timezone

from fastapi import APIRouter

from app.adapters.email import SmtpEmailProvider
from app.api.deps import AdminUser, SessionDep
from app.core.crypto import decrypt, encrypt
from app.models.settings import EmailSettings
from app.schemas.entities import (
    EmailSettingsRead,
    EmailSettingsUpdate,
    EmailTestRequest,
    EmailTestResult,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


def _get_or_create(session: SessionDep) -> EmailSettings:
    cfg = session.get(EmailSettings, 1)
    if cfg is None:
        cfg = EmailSettings(id=1)
        session.add(cfg)
        session.commit()
        session.refresh(cfg)
    return cfg


def _to_read(cfg: EmailSettings) -> EmailSettingsRead:
    return EmailSettingsRead(
        provider=cfg.provider,
        host=cfg.host,
        port=cfg.port,
        use_tls=cfg.use_tls,
        username=cfg.username,
        from_name=cfg.from_name,
        from_email=cfg.from_email,
        enabled=cfg.enabled,
        password_set=bool(cfg.password_encrypted),
        updated_at=cfg.updated_at,
    )


@router.get("/email", response_model=EmailSettingsRead)
def get_email_settings(session: SessionDep, _: AdminUser):
    return _to_read(_get_or_create(session))


@router.put("/email", response_model=EmailSettingsRead)
def update_email_settings(payload: EmailSettingsUpdate, session: SessionDep, _: AdminUser):
    cfg = _get_or_create(session)
    data = payload.model_dump(exclude_unset=True)

    # Password is handled specially: omitted -> keep, "" -> clear, else encrypt.
    if "password" in data:
        pw = data.pop("password")
        if pw is None:
            pass  # keep existing
        elif pw == "":
            cfg.password_encrypted = None
        else:
            cfg.password_encrypted = encrypt(pw)

    for key, value in data.items():
        setattr(cfg, key, value)
    cfg.updated_at = datetime.now(timezone.utc)

    session.add(cfg)
    session.commit()
    session.refresh(cfg)
    return _to_read(cfg)


@router.post("/email/test", response_model=EmailTestResult)
def send_test_email(payload: EmailTestRequest, session: SessionDep, _: AdminUser):
    cfg = _get_or_create(session)
    if not cfg.username or not cfg.password_encrypted:
        return EmailTestResult(status="failed", detail="לא הוגדרו שם משתמש וסיסמה")
    password = decrypt(cfg.password_encrypted)
    if not password:
        return EmailTestResult(
            status="failed", detail="לא ניתן לפענח את הסיסמה השמורה (ייתכן ש-SECRET_KEY השתנה)"
        )

    provider = SmtpEmailProvider(
        host=cfg.host,
        port=cfg.port,
        username=cfg.username,
        password=password,
        from_email=cfg.from_email or cfg.username,
        from_name=cfg.from_name,
        use_tls=cfg.use_tls,
    )
    result = provider.send(
        payload.to,
        "בדיקת חיבור דוא״ל — פנסיון בשדות",
        "הודעת בדיקה. אם קיבלת אותה, חיבור הדוא״ל של המערכת פעיל.",
    )
    if result.status == "sent":
        return EmailTestResult(status="sent", detail=f"נשלח אל {payload.to}")
    return EmailTestResult(status="failed", detail=result.provider_reference)
