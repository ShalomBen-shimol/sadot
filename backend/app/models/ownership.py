from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.base import utcnow
from app.models.enums import OwnershipTransferStatus, TransferType


class OwnershipTransfer(SQLModel, table=True):
    __tablename__ = "ownership_transfers"

    id: int | None = Field(default=None, primary_key=True)
    dog_id: int = Field(foreign_key="dogs.id", index=True)
    from_person_id: int | None = Field(default=None, foreign_key="people.id")
    to_person_id: int | None = Field(default=None, foreign_key="people.id")
    # Authorities are resolved from the surrenderer's and receiver's municipality.
    from_authority_id: int | None = Field(default=None, foreign_key="municipalities.id")
    to_authority_id: int | None = Field(default=None, foreign_key="municipalities.id")

    transfer_type: TransferType
    status: OwnershipTransferStatus = Field(
        default=OwnershipTransferStatus.draft, index=True
    )

    sent_to_authority_at: datetime | None = None
    confirmed_at: datetime | None = None
    last_followup_at: datetime | None = None
    next_followup_at: datetime | None = Field(default=None, index=True)
    notes: str | None = None
    # Index of the current step in the active TransferWorkflow for this type.
    workflow_step: int = Field(default=0)
    created_at: datetime = Field(default_factory=utcnow)
