"""add email_settings table (admin-configured outbound email account)

Idempotent (guards against an existing table) so `alembic upgrade head` is a
clean no-op on any DB where SQLModel create_all already built it.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-30
"""
from typing import Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if not _has_table("email_settings"):
        op.create_table(
            "email_settings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("provider", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("host", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("port", sa.Integer(), nullable=False),
            sa.Column("use_tls", sa.Boolean(), nullable=False),
            sa.Column("username", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column("password_encrypted", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column("from_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column("from_email", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    if _has_table("email_settings"):
        op.drop_table("email_settings")
