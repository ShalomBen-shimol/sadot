"""Digital-signature abstraction. Phase 1 = mock only."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class SignatureSession:
    sign_url: str
    provider_reference: str


class SignatureProvider(ABC):
    name: str

    @abstractmethod
    def create_request(self, signer_name: str, document_title: str) -> SignatureSession: ...


class MockSignatureProvider(SignatureProvider):
    name = "mock"

    def create_request(self, signer_name: str, document_title: str) -> SignatureSession:
        ref = f"mock-sig-{abs(hash((signer_name, document_title))) % 10**8}"
        return SignatureSession(
            sign_url=f"https://sign.mock.local/{ref}",
            provider_reference=ref,
        )


def get_signature_provider() -> SignatureProvider:
    if settings.signature_provider_key:
        pass  # return RealSignatureProvider(...)
    return MockSignatureProvider()
