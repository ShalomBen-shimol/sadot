"""Standard CRUD routers for the simpler entities."""
from app.api.v1.crud import build_crud_router
from app.models.municipality import Municipality
from app.models.person import Person
from app.models.support import Document, Message, SignatureRequest, Task
from app.schemas.entities import (
    DocumentCreate,
    MessageCreate,
    MunicipalityCreate,
    MunicipalityUpdate,
    PersonCreate,
    PersonUpdate,
    SignatureRequestCreate,
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
)

documents_router = build_crud_router(
    model=Document,
    create_schema=DocumentCreate,
    update_schema=DocumentCreate,
    prefix="/documents",
    tag="documents",
)

signatures_router = build_crud_router(
    model=SignatureRequest,
    create_schema=SignatureRequestCreate,
    update_schema=SignatureRequestCreate,
    prefix="/signatures",
    tag="signatures",
)

messages_router = build_crud_router(
    model=Message,
    create_schema=MessageCreate,
    update_schema=MessageCreate,
    prefix="/messages",
    tag="messages",
)
