"""Public (unauthenticated) endpoints: adoption listings + lead intake.

These endpoints expose ONLY non-sensitive data and accept privacy-consented leads.
"""
from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from app.api.deps import SessionDep
from app.models.dog import Dog, DogPhoto
from app.models.enums import DogStatus
from app.schemas.entities import (
    AdoptionLeadIn,
    DogPublic,
    LeadResponse,
    SurrenderLeadIn,
)
from app.services import leads as lead_service

router = APIRouter(prefix="/public", tags=["public"])

# Statuses considered "listable" on the public adoption page.
PUBLIC_STATUSES = {DogStatus.available_for_adoption, DogStatus.reserved}


def _to_public(session: SessionDep, dog: Dog) -> DogPublic:
    photos = session.exec(select(DogPhoto).where(DogPhoto.dog_id == dog.id)).all()
    return DogPublic(
        id=dog.id,
        name=dog.name,
        breed=dog.breed,
        age=dog.age,
        gender=dog.gender,
        size=dog.size,
        color=dog.color,
        good_with_children=dog.good_with_children,
        good_with_dogs=dog.good_with_dogs,
        good_with_cats=dog.good_with_cats,
        suitable_for_apartment=dog.suitable_for_apartment,
        suitable_for_first_time_owner=dog.suitable_for_first_time_owner,
        public_description=dog.public_description,
        public_area=dog.public_area,
        current_location_type=dog.current_location_type,
        status=dog.status,
        photos=[p.file_url for p in sorted(photos, key=lambda x: not x.is_primary)],
    )


@router.get("/dogs", response_model=list[DogPublic])
def public_dogs(session: SessionDep, offset: int = 0, limit: int = Query(50, le=200)):
    dogs = session.exec(
        select(Dog).where(Dog.status == DogStatus.available_for_adoption).offset(offset).limit(limit)
    ).all()
    return [_to_public(session, d) for d in dogs]


@router.get("/dogs/{dog_id}", response_model=DogPublic)
def public_dog(dog_id: int, session: SessionDep):
    dog = session.get(Dog, dog_id)
    if not dog or dog.status not in PUBLIC_STATUSES:
        raise HTTPException(status_code=404, detail="Dog not available")
    return _to_public(session, dog)


@router.post("/leads/surrender", response_model=LeadResponse)
def submit_surrender_lead(payload: SurrenderLeadIn, session: SessionDep):
    if not payload.consent_privacy:
        raise HTTPException(status_code=422, detail="Privacy consent required")
    person, case = lead_service.intake_surrender(session, payload)
    return LeadResponse(detail="הליד התקבל, ניצור קשר בקרוב", person_id=person.id, case_id=case.id)


@router.post("/leads/adoption", response_model=LeadResponse)
def submit_adoption_lead(payload: AdoptionLeadIn, session: SessionDep):
    if not payload.consent_privacy:
        raise HTTPException(status_code=422, detail="Privacy consent required")
    person, lead = lead_service.intake_adoption(session, payload)
    return LeadResponse(detail="פנייתך התקבלה, ניצור קשר בקרוב", person_id=person.id, lead_id=lead.id)
