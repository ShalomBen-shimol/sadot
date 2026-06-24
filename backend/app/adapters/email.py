"""Email abstraction (SMTP). Phase 1 = mock only."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.config import settings
from app.core.logging import logger


@dataclass
class EmailResult:
    provider_reference: str
    status: str


class EmailProvider(ABC):
    name: str

    @abstractmethod
    def send(self, to: str, subject: str, body: str, attachments: list[str] | None = None) -> EmailResult: ...


class MockEmailProvider(EmailProvider):
    name = "mock"

    def send(self, to: str, subject: str, body: str, attachments: list[str] | None = None) -> EmailResult:
        att = f" (+{len(attachments)} attachments)" if attachments else ""
        logger.info("[MOCK EMAIL] -> %s | %s%s", to, subject, att)
        return EmailResult(provider_reference=f"mock-email-{abs(hash((to, subject))) % 10**8}", status="sent")


def get_email_provider() -> EmailProvider:
    if settings.smtp_host:
        pass  # return SmtpEmailProvider(...)
    return MockEmailProvider()
