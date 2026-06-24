"""Import all models so SQLModel.metadata is fully populated."""
from app.models.adoption import AdoptionCase, AdoptionLead
from app.models.dog import Dog, DogPhoto
from app.models.municipality import Municipality
from app.models.ownership import OwnershipTransfer
from app.models.person import Person
from app.models.support import (
    AuditLog,
    Document,
    Message,
    SignatureRequest,
    Task,
)
from app.models.surrender import SubscriptionPayment, SurrenderCase
from app.models.user import User

__all__ = [
    "AdoptionCase",
    "AdoptionLead",
    "AuditLog",
    "Dog",
    "DogPhoto",
    "Document",
    "Message",
    "Municipality",
    "OwnershipTransfer",
    "Person",
    "SignatureRequest",
    "SubscriptionPayment",
    "SurrenderCase",
    "Task",
    "User",
]
