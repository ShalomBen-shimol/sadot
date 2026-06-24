"""Audit logging — records every meaningful action and sensitive access."""
import json

from sqlmodel import Session

from app.models.support import AuditLog


def log(
    session: Session,
    *,
    action: str,
    actor_user_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=json.dumps(metadata, ensure_ascii=False) if metadata else None,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry
