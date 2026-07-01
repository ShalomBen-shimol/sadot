"""Owner-configurable ownership-transfer workflow.

One active TransferWorkflow per transfer_type defines the ordered steps the
engine walks. `steps` is a JSON list of {type, title, config, manual?} — see
app/services/workflow.py for the step vocabulary and engine. Versioned like the
bot config (each save is a new row; one active per type)."""
from datetime import datetime, timezone

from sqlalchemy import Column
from sqlalchemy import JSON as SA_JSON
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TransferWorkflow(SQLModel, table=True):
    __tablename__ = "transfer_workflows"

    id: int | None = Field(default=None, primary_key=True)
    transfer_type: str = Field(index=True)  # matches enums.TransferType values
    version: int = Field(default=1, index=True)
    is_active: bool = Field(default=False, index=True)
    steps: list = Field(default_factory=list, sa_column=Column(SA_JSON))
    created_by_user_id: int | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=_utcnow)
