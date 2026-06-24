from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, SessionDep
from app.models.dog import Dog, DogPhoto
from app.models.enums import DogStatus
from app.repositories.base import CRUDRepository
from app.schemas.common import StatusTransition
from app.schemas.entities import DogCreate, DogUpdate

router = APIRouter(prefix="/dogs", tags=["dogs"])
repo = CRUDRepository(Dog)


@router.get("", response_model=list[Dog])
def list_dogs(
    session: SessionDep,
    _: CurrentUser,
    status_filter: DogStatus | None = Query(default=None, alias="status"),
    offset: int = 0,
    limit: int = Query(default=100, le=500),
):
    filters = {"status": status_filter} if status_filter else None
    return repo.list(session, offset=offset, limit=limit, filters=filters)


@router.get("/{dog_id}", response_model=Dog)
def get_dog(dog_id: int, session: SessionDep, _: CurrentUser):
    dog = repo.get(session, dog_id)
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    return dog


@router.post("", response_model=Dog, status_code=status.HTTP_201_CREATED)
def create_dog(payload: DogCreate, session: SessionDep, _: CurrentUser):
    return repo.create(session, payload.model_dump(exclude_unset=True))


@router.patch("/{dog_id}", response_model=Dog)
def update_dog(dog_id: int, payload: DogUpdate, session: SessionDep, _: CurrentUser):
    dog = repo.get(session, dog_id)
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    return repo.update(session, dog, payload.model_dump(exclude_unset=True))


@router.post("/{dog_id}/status", response_model=Dog)
def set_status(dog_id: int, payload: StatusTransition, session: SessionDep, _: CurrentUser):
    dog = repo.get(session, dog_id)
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    try:
        dog.status = DogStatus(payload.status)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid status")
    return repo.save(session, dog)


@router.get("/{dog_id}/photos", response_model=list[DogPhoto])
def list_photos(dog_id: int, session: SessionDep, _: CurrentUser):
    return CRUDRepository(DogPhoto).list(session, filters={"dog_id": dog_id})


@router.post("/{dog_id}/photos", response_model=DogPhoto, status_code=status.HTTP_201_CREATED)
def add_photo(dog_id: int, file_url: str, session: SessionDep, _: CurrentUser, is_primary: bool = False):
    if not repo.get(session, dog_id):
        raise HTTPException(status_code=404, detail="Dog not found")
    return CRUDRepository(DogPhoto).create(
        session, {"dog_id": dog_id, "file_url": file_url, "is_primary": is_primary}
    )
