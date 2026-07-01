"""Import all models so SQLModel.metadata is fully populated."""
from app.models.adoption import AdoptionCase, AdoptionLead
from app.models.chat import BotConfig, ChatMessage, Conversation
from app.models.dog import Dog, DogPhoto
from app.models.municipality import Locality, Municipality
from app.models.ownership import OwnershipTransfer
from app.models.person import Person
from app.models.settings import EmailSettings
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
    "BotConfig",
    "ChatMessage",
    "Conversation",
    "Dog",
    "DogPhoto",
    "Document",
    "EmailSettings",
    "Locality",
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
