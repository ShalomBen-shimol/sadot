"""Resolve the veterinary authority for a given locality (יישוב).

Resolution goes through the Locality table (every יישוב in Israel is linked to
its authority); we fall back to a direct authority-name match for robustness.
"""
import re

from sqlmodel import Session, select

from app.models.municipality import Locality, Municipality


def normalize_name(s: str | None) -> str:
    """Tolerant normalization for locality lookup (quotes, hyphens, spelling)."""
    if not s:
        return ""
    s = str(s).strip()
    s = s.replace("״", '"').replace("׳", "'").replace("`", "'")
    s = s.replace("־", "-").replace("–", "-").replace("—", "-")
    s = re.sub(r"\s*\([^)]*\)", "", s)        # drop parentheticals
    s = s.replace("קריית", "קרית")            # unify קרית / קריית
    s = re.sub(r"\s*-\s*", "-", s)            # unify hyphen spacing
    s = re.sub(r"\s+", " ", s)
    s = s.replace("תל אביב-יפו", "תל אביב").replace("תל אביב -יפו", "תל אביב")
    return s.strip()


def resolve_by_city(session: Session, city: str | None) -> Municipality | None:
    """Return the veterinary authority serving a given locality name."""
    if not city:
        return None
    q = normalize_name(city)
    if not q:
        return None

    # 1) Resolve via the locality -> authority link.
    loc = session.exec(
        select(Locality).where(Locality.name_normalized == q)
    ).first()
    if loc and loc.municipality_id:
        muni = session.get(Municipality, loc.municipality_id)
        if muni and muni.is_active:
            return muni

    # 2) Fallback: the input is itself an authority name (רשות).
    muni = session.exec(
        select(Municipality).where(
            Municipality.city_name == city.strip(),
            Municipality.is_active == True,  # noqa: E712
        )
    ).first()
    return muni
