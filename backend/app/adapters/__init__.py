"""External-integration adapters.

Each integration has an abstract Provider and a Mock implementation. The active
provider is chosen by `get_*_provider()` based on whether a real credential is
configured in settings. In phase 1 everything resolves to the mock.
"""
from app.adapters.email import EmailProvider, get_email_provider
from app.adapters.messaging import MessagingProvider, get_messaging_provider
from app.adapters.monday import MondayAdapter, get_monday_adapter
from app.adapters.payment import PaymentProvider, get_payment_provider
from app.adapters.signature import SignatureProvider, get_signature_provider

__all__ = [
    "EmailProvider",
    "MessagingProvider",
    "MondayAdapter",
    "PaymentProvider",
    "SignatureProvider",
    "get_email_provider",
    "get_messaging_provider",
    "get_monday_adapter",
    "get_payment_provider",
    "get_signature_provider",
]
