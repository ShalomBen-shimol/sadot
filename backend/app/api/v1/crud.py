"""Factory that builds a standard CRUD router for a SQLModel table."""
from typing import Type

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import SQLModel

from app.api.deps import CurrentUser, SessionDep
from app.repositories.base import CRUDRepository


def build_crud_router(
    *,
    model: Type[SQLModel],
    create_schema: Type[BaseModel],
    update_schema: Type[BaseModel],
    prefix: str,
    tag: str,
    filter_fields: list[str] | None = None,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])
    repo = CRUDRepository(model)
    filter_fields = filter_fields or []

    @router.get("", response_model=list[model])
    def list_items(
        session: SessionDep,
        _: CurrentUser,
        offset: int = 0,
        limit: int = Query(default=100, le=500),
    ):
        return repo.list(session, offset=offset, limit=limit)

    @router.get("/{item_id}", response_model=model)
    def get_item(item_id: int, session: SessionDep, _: CurrentUser):
        obj = repo.get(session, item_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{tag} not found")
        return obj

    @router.post("", response_model=model, status_code=status.HTTP_201_CREATED)
    def create_item(payload: create_schema, session: SessionDep, _: CurrentUser):
        return repo.create(session, payload.model_dump(exclude_unset=True))

    @router.patch("/{item_id}", response_model=model)
    def update_item(item_id: int, payload: update_schema, session: SessionDep, _: CurrentUser):
        obj = repo.get(session, item_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{tag} not found")
        return repo.update(session, obj, payload.model_dump(exclude_unset=True))

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_item(item_id: int, session: SessionDep, _: CurrentUser):
        obj = repo.get(session, item_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{tag} not found")
        repo.delete(session, obj)

    return router
