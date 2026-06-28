"""Pytest fixtures: isolated in-memory DB shared by the API client and a
direct DB session, plus auth helpers.

Each test gets a fresh in-memory SQLite engine (StaticPool so every connection
sees the same in-memory database), tables created and seed data loaded. The
FastAPI `get_session` dependency is overridden to use this engine, and the
TestClient is created WITHOUT entering the lifespan context so the real
scheduler and the on-disk sadot.db are never touched.
"""
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

import app.models  # noqa: F401  (register tables on SQLModel.metadata)
from app.core.database import get_session
from app.db.seed import seed
from app.main import app


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed(session)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(name="db_session")
def db_session_fixture(engine) -> Generator[Session, None, None]:
    """Direct DB session for arrange/assert that bypasses the HTTP layer."""
    with Session(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine) -> Generator[TestClient, None, None]:
    def override_get_session() -> Generator[Session, None, None]:
        with Session(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    # No `with` block: skip lifespan (scheduler + real DB seed) entirely.
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="admin_token")
def admin_token_fixture(client: TestClient) -> str:
    r = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@sadot.local", "password": "admin1234"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(name="auth")
def auth_fixture(admin_token: str) -> dict[str, str]:
    """Authorization header dict for the seeded admin."""
    return {"Authorization": f"Bearer {admin_token}"}
