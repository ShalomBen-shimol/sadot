"""Aggregate v1 API router."""
from fastapi import APIRouter

from app.api.v1 import (
    adoption,
    auth,
    backoffice,
    dashboard,
    documents,
    dogs,
    integrations,
    localities,
    ownership,
    public,
    qr,
    signatures,
    surrender,
)
from app.api.v1.generic_routers import (
    messages_router,
    municipalities_router,
    people_router,
    tasks_router,
)

api_router = APIRouter(prefix="/api/v1")

# Auth
api_router.include_router(auth.router)

# Public (unauthenticated)
api_router.include_router(public.router)

# Back-office
api_router.include_router(dashboard.router)
api_router.include_router(dogs.router)
api_router.include_router(people_router)
api_router.include_router(surrender.router)
api_router.include_router(adoption.router)
api_router.include_router(ownership.router)
api_router.include_router(municipalities_router)
api_router.include_router(localities.router)
api_router.include_router(tasks_router)
api_router.include_router(documents.router)
api_router.include_router(signatures.router)
api_router.include_router(messages_router)
api_router.include_router(qr.router)
api_router.include_router(integrations.router)

# Back-office aggregate case-file endpoints (people/dogs/transfers)
api_router.include_router(backoffice.router)
