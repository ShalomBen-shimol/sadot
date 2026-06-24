"""Payment abstraction. Phase 1 = mock only (no real charging)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.config import settings
from app.core.logging import logger


@dataclass
class ChargeResult:
    provider_reference: str
    status: str  # "paid" / "failed"


@dataclass
class CheckoutLink:
    url: str
    provider_reference: str


class PaymentProvider(ABC):
    name: str

    @abstractmethod
    def create_checkout(self, amount: float, description: str) -> CheckoutLink: ...

    @abstractmethod
    def charge(self, amount: float, description: str) -> ChargeResult: ...


class MockPaymentProvider(PaymentProvider):
    name = "mock"

    def create_checkout(self, amount: float, description: str) -> CheckoutLink:
        ref = f"mock-pay-{abs(hash(description)) % 10**8}"
        return CheckoutLink(url=f"https://pay.mock.local/checkout/{ref}?amount={amount}", provider_reference=ref)

    def charge(self, amount: float, description: str) -> ChargeResult:
        logger.info("[MOCK PAYMENT] charge %s for %s", amount, description)
        return ChargeResult(provider_reference=f"mock-charge-{abs(hash(description)) % 10**8}", status="paid")


def get_payment_provider() -> PaymentProvider:
    if settings.payment_provider_key:
        pass  # return RealPaymentProvider(...)
    return MockPaymentProvider()
