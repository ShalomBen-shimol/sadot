"""Back-office dashboard aggregates."""
from fastapi import APIRouter
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models.adoption import AdoptionCase, AdoptionLead
from app.models.dog import Dog
from app.models.enums import DogStatus, OwnershipTransferStatus, TaskStatus
from app.models.ownership import OwnershipTransfer
from app.models.surrender import SurrenderCase
from app.models.support import Task

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _count(session, model, *where) -> int:
    statement = select(func.count()).select_from(model)
    for clause in where:
        statement = statement.where(clause)
    return session.exec(statement).one()


@router.get("/summary")
def summary(session: SessionDep, _: CurrentUser):
    return {
        "dogs_total": _count(session, Dog),
        "dogs_available": _count(session, Dog, Dog.status == DogStatus.available_for_adoption),
        "dogs_in_facility": _count(session, Dog, Dog.status == DogStatus.in_facility),
        "dogs_adopted": _count(session, Dog, Dog.status == DogStatus.adopted),
        "surrender_cases": _count(session, SurrenderCase),
        "adoption_leads": _count(session, AdoptionLead),
        "adoption_cases": _count(session, AdoptionCase),
        "open_tasks": _count(session, Task, Task.status == TaskStatus.open),
        "transfers_awaiting_authority": _count(
            session,
            OwnershipTransfer,
            OwnershipTransfer.status.in_(  # type: ignore[attr-defined]
                [OwnershipTransferStatus.sent_to_authority, OwnershipTransferStatus.followup_required]
            ),
        ),
    }
