"""Surrender workflows: facility hand-off and 'home subscription' (מסירה מהבית)."""
from datetime import date

from sqlmodel import Session, select

from app.adapters import get_payment_provider
from app.core.config import settings
from app.models.dog import Dog
from app.models.enums import (
    DogStatus,
    LocationType,
    PaymentStatus,
    SurrenderStatus,
    SurrenderType,
    TransferType,
)
from app.models.surrender import SubscriptionPayment, SurrenderCase
from app.services import ownership as ownership_service


def create_case(session: Session, data: dict) -> SurrenderCase:
    surrender_type = data.get("surrender_type", SurrenderType.facility)
    case = SurrenderCase(**data)

    if surrender_type == SurrenderType.home_subscription:
        case.monthly_price = settings.home_subscription_monthly_price
        # Accumulated credit grows monthly toward the facility total.
        case.total_required_amount = settings.facility_total_amount
    else:
        case.total_required_amount = settings.facility_total_amount

    session.add(case)
    session.commit()
    session.refresh(case)
    return case


def _set_dog_status(session: Session, dog_id: int | None, status: DogStatus, location: LocationType) -> None:
    if not dog_id:
        return
    dog = session.get(Dog, dog_id)
    if dog:
        dog.status = status
        dog.current_location_type = location
        session.add(dog)
        session.commit()


def recompute_credit(session: Session, case: SurrenderCase) -> float:
    """Accumulated credit = sum of paid subscription payments."""
    payments = session.exec(
        select(SubscriptionPayment).where(
            SubscriptionPayment.surrender_case_id == case.id,
            SubscriptionPayment.status == PaymentStatus.paid,
        )
    ).all()
    case.accumulated_credit = sum(p.amount for p in payments)
    session.add(case)
    session.commit()
    session.refresh(case)
    return case.accumulated_credit


def record_subscription_payment(
    session: Session, case: SurrenderCase, month_index: int
) -> SubscriptionPayment:
    """Charge (mock) one monthly subscription payment and update credit."""
    provider = get_payment_provider()
    charge = provider.charge(case.monthly_price or 0, f"home-subscription case {case.id} month {month_index}")
    payment = SubscriptionPayment(
        surrender_case_id=case.id,
        amount=case.monthly_price or 0,
        month_index=month_index,
        payment_date=date.today(),
        status=PaymentStatus.paid if charge.status == "paid" else PaymentStatus.failed,
        payment_provider_reference=charge.provider_reference,
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)
    recompute_credit(session, case)
    return payment


def activate_home_subscription(session: Session, case: SurrenderCase) -> SurrenderCase:
    """Start the monthly subscription; dog stays home but is listed for adoption."""
    next_month = _next_month_index(session, case)
    record_subscription_payment(session, case, next_month)
    case.start_date = case.start_date or date.today()
    case.status = SurrenderStatus.active_home_subscription
    _set_dog_status(session, case.dog_id, DogStatus.available_for_adoption, LocationType.home)
    session.add(case)
    session.commit()
    session.refresh(case)
    return case


def _next_month_index(session: Session, case: SurrenderCase) -> int:
    existing = session.exec(
        select(SubscriptionPayment).where(SubscriptionPayment.surrender_case_id == case.id)
    ).all()
    return len(existing) + 1


def start_facility_transfer(session: Session, case: SurrenderCase):
    """Open ownership transfer surrenderer -> facility and a follow-up task."""
    case.status = SurrenderStatus.ownership_transfer_in_progress
    session.add(case)
    session.commit()
    transfer = ownership_service.create_transfer(
        session,
        {
            "dog_id": case.dog_id,
            "from_person_id": case.surrenderer_person_id,
            "to_person_id": None,  # facility is the receiver (no Person row in phase 1)
            "transfer_type": TransferType.surrender_to_facility,
        },
        from_city=_surrenderer_city(session, case),
        to_city=None,
    )
    _set_dog_status(session, case.dog_id, DogStatus.pending_surrender, LocationType.facility)
    return transfer


def _surrenderer_city(session: Session, case: SurrenderCase) -> str | None:
    from app.models.person import Person

    person = session.get(Person, case.surrenderer_person_id)
    return person.city if person else None


def convert_home_to_facility(session: Session, case: SurrenderCase):
    """After ~7 months the accrued credit covers a facility surrender."""
    case.surrender_type = SurrenderType.facility
    return start_facility_transfer(session, case)
