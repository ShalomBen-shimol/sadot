"""Generic CRUD repository over a SQLModel table."""
from typing import Generic, TypeVar

from sqlmodel import Session, SQLModel, select

ModelT = TypeVar("ModelT", bound=SQLModel)


class CRUDRepository(Generic[ModelT]):
    def __init__(self, model: type[ModelT]):
        self.model = model

    def get(self, session: Session, obj_id: int) -> ModelT | None:
        return session.get(self.model, obj_id)

    def list(
        self,
        session: Session,
        *,
        offset: int = 0,
        limit: int = 100,
        filters: dict | None = None,
    ) -> list[ModelT]:
        statement = select(self.model)
        for field, value in (filters or {}).items():
            if value is not None and hasattr(self.model, field):
                statement = statement.where(getattr(self.model, field) == value)
        statement = statement.offset(offset).limit(limit)
        return list(session.exec(statement).all())

    def create(self, session: Session, data: dict) -> ModelT:
        obj = self.model(**data)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    def save(self, session: Session, obj: ModelT) -> ModelT:
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    def update(self, session: Session, obj: ModelT, data: dict) -> ModelT:
        # `data` comes from `model_dump(exclude_unset=True)`, so it contains only
        # the fields the client actually sent. Apply them all — including explicit
        # nulls — so a field can be cleared back to empty, not just overwritten.
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        return self.save(session, obj)

    def delete(self, session: Session, obj: ModelT) -> None:
        session.delete(obj)
        session.commit()
