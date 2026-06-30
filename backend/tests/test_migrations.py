"""Alembic migration safety.

env.py reads the DB url from settings.database_url, so we point it at a temp
SQLite file per test by monkeypatching that setting, then drive alembic via its
command API.

Two paths matter:
  1. fresh DB -> `upgrade head` builds the full current schema.
  2. prod-like DB -> the schema already exists (built by SQLModel create_all)
     and alembic is stamped at the initial revision; `upgrade head` must be a
     clean no-op, NOT a DuplicateColumn/DuplicateTable error.
"""
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlmodel import SQLModel

import app.models  # noqa: F401  (register tables on SQLModel.metadata)
from app.core.config import settings

BACKEND_DIR = Path(__file__).resolve().parents[1]
INITIAL_REVISION = "34a8b230b103"


def _alembic_config(url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)  # env.py overrides via settings too
    return cfg


def test_upgrade_head_on_fresh_db(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'fresh.db'}"
    monkeypatch.setattr(settings, "database_url", url)

    command.upgrade(_alembic_config(url), "head")

    insp = sa.inspect(sa.create_engine(url))
    assert "localities" in insp.get_table_names()
    muni_cols = {c["name"] for c in insp.get_columns("municipalities")}
    assert {"vet_name", "license_number"} <= muni_cols


def test_upgrade_head_is_idempotent_over_create_all(tmp_path, monkeypatch):
    """Reproduces the live box: full schema already present + stamped at initial."""
    url = f"sqlite:///{tmp_path / 'prod.db'}"
    monkeypatch.setattr(settings, "database_url", url)

    engine = sa.create_engine(url)
    SQLModel.metadata.create_all(engine)  # what production's create_all does

    cfg = _alembic_config(url)
    command.stamp(cfg, INITIAL_REVISION)  # production was stamped here
    # Must not raise even though vet_name/license_number/localities already exist.
    command.upgrade(cfg, "head")

    insp = sa.inspect(engine)
    assert "localities" in insp.get_table_names()
    muni_cols = {c["name"] for c in insp.get_columns("municipalities")}
    assert {"vet_name", "license_number"} <= muni_cols
