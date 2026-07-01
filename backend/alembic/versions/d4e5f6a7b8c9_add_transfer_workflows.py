"""add transfer_workflows table + ownership_transfers.workflow_step

Idempotent — guards against existing objects, so `alembic upgrade head` is a
clean no-op where create_all already applied them, while adding them on a DB
that lacks them (create_all cannot ALTER an existing table, so the column add
here is what actually lands on the live DB).

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-01
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    if table not in insp.get_table_names():
        return False
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    if not _has_column("ownership_transfers", "workflow_step"):
        op.add_column(
            "ownership_transfers",
            sa.Column("workflow_step", sa.Integer(), nullable=False, server_default="0"),
        )

    if not _has_table("transfer_workflows"):
        op.create_table(
            "transfer_workflows",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("transfer_type", sa.String(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("steps", sa.JSON(), nullable=True),
            sa.Column("created_by_user_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("transfer_workflows", schema=None) as b:
            b.create_index(b.f("ix_transfer_workflows_transfer_type"), ["transfer_type"], unique=False)
            b.create_index(b.f("ix_transfer_workflows_version"), ["version"], unique=False)
            b.create_index(b.f("ix_transfer_workflows_is_active"), ["is_active"], unique=False)


def downgrade() -> None:
    if _has_table("transfer_workflows"):
        op.drop_table("transfer_workflows")
    if _has_column("ownership_transfers", "workflow_step"):
        op.drop_column("ownership_transfers", "workflow_step")
