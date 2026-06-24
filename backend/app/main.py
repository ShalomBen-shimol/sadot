"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_db
from app.db.seed import seed_default
from app.tasks import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev convenience: create tables + seed. Production should rely on Alembic.
    init_db()
    seed_default()
    scheduler.start(app)
    yield
    await scheduler.stop(app)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="מערכת CRM ואוטומציה לפנסיון בשדות — שלב 1 (MVP).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "environment": settings.environment}
