"""Messaging abstraction (WhatsApp / SMS). Phase 1 = mock only."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.config import settings
from app.core.logging import logger


@dataclass
class SendResult:
    provider_reference: str
    status: str  # "sent" / "failed"


class MessagingProvider(ABC):
    name: str

    @abstractmethod
    def send(self, to_phone: str, content: str) -> SendResult: ...


class MockMessagingProvider(MessagingProvider):
    name = "mock"

    def send(self, to_phone: str, content: str) -> SendResult:
        # No real delivery — just log for traceability.
        logger.info("[MOCK WHATSAPP] -> %s: %s", to_phone, content[:120])
        return SendResult(provider_reference=f"mock-msg-{abs(hash((to_phone, content))) % 10**8}", status="sent")


# Placeholder for the future real implementation.
# class WhatsAppProvider(MessagingProvider): ...


def get_messaging_provider() -> MessagingProvider:
    if settings.whatsapp_api_token:
        # return WhatsAppProvider(settings.whatsapp_api_token)
        pass
    return MockMessagingProvider()
