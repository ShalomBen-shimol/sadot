"""Resolve the veterinary authority for a given locality."""
from sqlmodel import Session, select

from app.models.municipality import Municipality


def resolve_by_city(session: Session, city: str | None) -> Municipality | None:
    if not city:
        return None
    city = city.strip()
    statement = select(Municipality).where(
        Municipality.city_name == city, Municipality.is_active == True  # noqa: E712
    )
    return session.exec(statement).first()
