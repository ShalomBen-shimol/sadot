"""Localities (יישובים) directory + authority resolution.

Every Israeli locality is linked to its veterinary authority. These endpoints
power the admin authorities page (search, manual assignment of the review
queue) and the public/agent "which authority serves this town?" lookup.
"""
from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models.municipality import Locality, Municipality
from app.schemas.entities import LocalityAssign
from app.services.municipality import normalize_name, resolve_by_city

router = APIRouter(prefix="/localities", tags=["localities"])


@router.get("")
def list_localities(
    session: SessionDep,
    _: CurrentUser,
    search: str | None = Query(default=None),
    needs_review: bool | None = Query(default=None),
    offset: int = 0,
    limit: int = Query(default=100, le=1000),
):
    """Search localities (tolerant name match) with an optional review filter."""
    stmt = select(Locality)
    count_stmt = select(func.count()).select_from(Locality)
    if needs_review is not None:
        stmt = stmt.where(Locality.needs_review == needs_review)
        count_stmt = count_stmt.where(Locality.needs_review == needs_review)
    if search:
        q = normalize_name(search)
        like = f"%{q}%"
        stmt = stmt.where(Locality.name_normalized.like(like))  # type: ignore[attr-defined]
        count_stmt = count_stmt.where(Locality.name_normalized.like(like))  # type: ignore[attr-defined]
    total = session.exec(count_stmt).one()
    items = session.exec(stmt.order_by(Locality.name).offset(offset).limit(limit)).all()
    return {"total": total, "items": items}


@router.get("/resolve")
def resolve(session: SessionDep, _: CurrentUser, city: str = Query(...)):
    """Resolve a locality name to its serving veterinary authority."""
    q = normalize_name(city)
    loc = session.exec(select(Locality).where(Locality.name_normalized == q)).first()
    authority = resolve_by_city(session, city)
    return {
        "query": city,
        "locality": loc,
        "authority": authority,
        "resolved": authority is not None,
    }


@router.get("/{locality_id}", response_model=Locality)
def get_locality(locality_id: int, session: SessionDep, _: CurrentUser):
    loc = session.get(Locality, locality_id)
    if not loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Locality not found")
    return loc


@router.patch("/{locality_id}", response_model=Locality)
def assign_locality(locality_id: int, payload: LocalityAssign, session: SessionDep, _: CurrentUser):
    """Manually (re)assign a locality to an authority; clears the review flag."""
    loc = session.get(Locality, locality_id)
    if not loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Locality not found")
    if payload.municipality_id is not None:
        if not session.get(Municipality, payload.municipality_id):
            raise HTTPException(status_code=422, detail="Unknown authority")
        loc.municipality_id = payload.municipality_id
        loc.needs_review = False
    if payload.needs_review is not None:
        loc.needs_review = payload.needs_review
    session.add(loc)
    session.commit()
    session.refresh(loc)
    return loc
