from datetime import date, datetime

from sqlmodel import Field, SQLModel

from app.models.base import utcnow
from app.models.enums import PaymentStatus, SurrenderStatus, SurrenderType


class SurrenderCase(SQLModel, table=True):
    __tablename__ = "surrender_cases"

    id: int | None = Field(default=None, primary_key=True)
    dog_id: int | None = Field(default=None, foreign_key="dogs.id", index=True)
    surrenderer_person_id: int = Field(foreign_key="people.id", index=True)

    surrender_type: SurrenderType = Field(default=SurrenderType.facility)
    monthly_price: float | None = None
    total_required_amount: float | None = None
    accumulated_credit: float = Field(default=0)

    start_date: date | None = None
    status: SurrenderStatus = Field(default=SurrenderStatus.new_lead, index=True)
    reason: str | None = None
    # Discreet handling requested by the surrenderer.
    privacy_required: bool = Field(default=False)
    # Owner agrees to be contacted directly by adopters (home subscription).
    allow_direct_contact: bool = Field(default=False)

    created_at: datetime = Field(default_factory=utcnow)


class SubscriptionPayment(SQLModel, table=True):
    __tablename__ = "subscription_payments"

    id: int | None = Field(default=None, primary_key=True)
    surrender_case_id: int = Field(foreign_key="surrender_cases.id", index=True)
    amount: float
    month_index: int  # 1-based month number within the subscription
    payment_date: date | None = None
    status: PaymentStatus = Field(default=PaymentStatus.pending)
    payment_provider_reference: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
