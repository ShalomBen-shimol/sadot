"""Standard CRUD routers for the simpler entities."""
from app.api.v1.crud import build_crud_router
from app.models.municipality import Municipality
from app.models.person import Person
from app.models.support import Message, Task
from app.schemas.entities import (
    MessageCreate,
    MunicipalityCreate,
    MunicipalityUpdate,
    PersonCreate,
    PersonUpdate,
    TaskCreateSchema,
    TaskUpdateSchema,
)

people_router = build_crud_router(
    model=Person,
    create_schema=PersonCreate,
    update_schema=PersonUpdate,
    prefix="/people",
    tag="people",
)

municipalities_router = build_crud_router(
    model=Municipality,
    create_schema=MunicipalityCreate,
    update_schema=MunicipalityUpdate,
    prefix="/municipalities",
    tag="municipalities",
)

tasks_router = build_crud_router(
    model=Task,
    create_schema=TaskCreateSchema,
    update_schema=TaskUpdateSchema,
    prefix="/tasks",
    tag="tasks",
    filter_fields=["status", "is_followup"],
)

messages_router = build_crud_router(
    model=Message,
    create_schema=MessageCreate,
    update_schema=MessageCreate,
    prefix="/messages",
    tag="messages",
)
