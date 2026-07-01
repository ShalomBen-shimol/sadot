"""add chatbot tables: conversations, chat_messages, bot_configs

Idempotent — each table is guarded, so `alembic upgrade head` is a clean no-op
on any DB where SQLModel create_all already built them (prod), while building
them on a fresh alembic-managed DB.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-01
"""
from typing import Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if not _has_table("conversations"):
        op.create_table(
            "conversations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("channel", sa.Enum("web", "whatsapp", name="conversationchannel"), nullable=False),
            sa.Column("goal", sa.Enum("surrender", "adopt", "general", name="conversationgoal"), nullable=False),
            sa.Column(
                "status",
                sa.Enum("active", "lead_created", "escalated", "closed", name="conversationstatus"),
                nullable=False,
            ),
            sa.Column("external_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column("person_id", sa.Integer(), nullable=True),
            sa.Column("surrender_case_id", sa.Integer(), nullable=True),
            sa.Column("collected", sa.JSON(), nullable=True),
            sa.Column("escalated", sa.Boolean(), nullable=False),
            sa.Column("summary", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["person_id"], ["people.id"]),
            sa.ForeignKeyConstraint(["surrender_case_id"], ["surrender_cases.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("conversations", schema=None) as b:
            b.create_index(b.f("ix_conversations_channel"), ["channel"], unique=False)
            b.create_index(b.f("ix_conversations_status"), ["status"], unique=False)
            b.create_index(b.f("ix_conversations_external_id"), ["external_id"], unique=False)
            b.create_index(b.f("ix_conversations_person_id"), ["person_id"], unique=False)
            b.create_index(b.f("ix_conversations_surrender_case_id"), ["surrender_case_id"], unique=False)
            b.create_index(b.f("ix_conversations_escalated"), ["escalated"], unique=False)

    if not _has_table("chat_messages"):
        op.create_table(
            "chat_messages",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("conversation_id", sa.Integer(), nullable=False),
            sa.Column("role", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("tool_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("chat_messages", schema=None) as b:
            b.create_index(b.f("ix_chat_messages_conversation_id"), ["conversation_id"], unique=False)

    if not _has_table("bot_configs"):
        op.create_table(
            "bot_configs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("persona", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("knowledgebase", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("model", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("created_by_user_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("bot_configs", schema=None) as b:
            b.create_index(b.f("ix_bot_configs_version"), ["version"], unique=False)
            b.create_index(b.f("ix_bot_configs_is_active"), ["is_active"], unique=False)


def downgrade() -> None:
    for t in ("chat_messages", "bot_configs", "conversations"):
        if _has_table(t):
            op.drop_table(t)
