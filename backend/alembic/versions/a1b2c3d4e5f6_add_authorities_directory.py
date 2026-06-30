"""add authorities directory: municipalities.vet_name/license_number + localities

These were originally added to production by SQLModel ``create_all`` (the DB was
wiped to pick them up), so the live schema already has them but the migration
history did not. This migration captures them as the real source of truth.

Every operation is guarded against existing objects so ``alembic upgrade head``
is a clean no-op on the live DB (where create_all already built them) while
still building them on any fresh, alembic-managed database.

Revision ID: a1b2c3d4e5f6
Revises: 34a8b230b103
Create Date: 2026-06-30
"""
from typing import Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "34a8b230b103"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    if table not in insp.get_table_names():
        return False
    return column in {c["name"] for c in insp.get_columns(table)}


def _has_index(table: str, index: str) -> bool:
    insp = sa.inspect(op.get_bind())
    if table not in insp.get_table_names():
        return False
    return index in {ix["name"] for ix in insp.get_indexes(table)}


def upgrade() -> None:
    # municipalities: new municipal-vet columns.
    if not _has_column("municipalities", "vet_name"):
        op.add_column(
            "municipalities",
            sa.Column("vet_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        )
    if not _has_column("municipalities", "license_number"):
        op.add_column(
            "municipalities",
            sa.Column("license_number", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        )

    # localities: brand-new table mapping every CBS locality to its authority.
    if not _has_table("localities"):
        op.create_table(
            "localities",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("name_normalized", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("symbol", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column("subdistrict", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column("district", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column("municipality_id", sa.Integer(), nullable=True),
            sa.Column("needs_review", sa.Boolean(), nullable=False),
            sa.ForeignKeyConstraint(["municipality_id"], ["municipalities.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    missing_indexes = [
        (col, idx)
        for col, idx in [
            ("name", "ix_localities_name"),
            ("name_normalized", "ix_localities_name_normalized"),
            ("symbol", "ix_localities_symbol"),
            ("municipality_id", "ix_localities_municipality_id"),
            ("needs_review", "ix_localities_needs_review"),
        ]
        if not _has_index("localities", idx)
    ]
    # Only open a batch context when there is work to do — an empty batch would
    # needlessly recreate the table on SQLite.
    if missing_indexes:
        with op.batch_alter_table("localities", schema=None) as batch_op:
            for col, idx in missing_indexes:
                batch_op.create_index(batch_op.f(idx), [col], unique=False)


def downgrade() -> None:
    if _has_table("localities"):
        op.drop_table("localities")
    if _has_column("municipalities", "license_number"):
        op.drop_column("municipalities", "license_number")
    if _has_column("municipalities", "vet_name"):
        op.drop_column("municipalities", "vet_name")
