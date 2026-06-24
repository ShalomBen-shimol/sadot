"""Aggregate v1 API router."""
from fastapi import APIRouter

from app.api.v1 import adoption, auth, dashboard, dogs, ownership, public, surrender
from app.api.v1.generic_routers import (
    documents_router,
    messages_router,
    municipalities_router,
    people_router,
    signatures_router,
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
api_router.include_router(tasks_router)
api_router.include_router(documents_router)
api_router.include_router(signatures_router)
api_router.include_router(messages_router)
