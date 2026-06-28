"""Aggregated case-file read endpoints for the back-office CRM screens.

Each endpoint gathers an entity together with everything linked to it so a
screen can be rendered from a single request. Auth-protected; admin-level
fields are allowed here (see schemas/backoffice).
"""
from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.models.dog import Dog
from app.models.ownership import OwnershipTransfer
from app.models.person import Person
from app.repositories.base import CRUDRepository
from app.schemas.backoffice import DogFile, OwnershipTransferDetail, PersonFile
from app.services import backoffice as backoffice_service

router = APIRouter(tags=["back-office"])

_person_repo = CRUDRepository(Person)
_dog_repo = CRUDRepository(Dog)
_transfer_repo = CRUDRepository(OwnershipTransfer)


@router.get("/people/{person_id}/file", response_model=PersonFile)
def person_file(person_id: int, session: SessionDep, _: CurrentUser):
    person = _person_repo.get(session, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return backoffice_service.build_person_file(session, person)


@router.get("/dogs/{dog_id}/file", response_model=DogFile)
def dog_file(dog_id: int, session: SessionDep, _: CurrentUser):
    dog = _dog_repo.get(session, dog_id)
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    return backoffice_service.build_dog_file(session, dog)


@router.get("/ownership-transfers/{transfer_id}/detail", response_model=OwnershipTransferDetail)
def ownership_transfer_detail(transfer_id: int, session: SessionDep, _: CurrentUser):
    transfer = _transfer_repo.get(session, transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return backoffice_service.build_transfer_detail(session, transfer)
