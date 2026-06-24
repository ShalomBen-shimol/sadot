"""monday.com CRM adapter — interface only in phase 1.

Documents what will need to sync later: leads, dogs, adoption cases, status
updates. With no MONDAY_API_TOKEN configured, sync is a no-op that records intent.
"""
from abc import ABC, abstractmethod

from app.core.config import settings


class MondayAdapter(ABC):
    name: str

    @abstractmethod
    def sync_lead(self, payload: dict) -> dict: ...

    @abstractmethod
    def sync_dog(self, payload: dict) -> dict: ...

    @abstractmethod
    def sync_adoption_case(self, payload: dict) -> dict: ...

    @abstractmethod
    def push_status_update(self, entity: str, entity_id: int, status: str) -> dict: ...


class MockMondayAdapter(MondayAdapter):
    name = "mock"

    def sync_lead(self, payload: dict) -> dict:
        return {"synced": False, "reason": "mock", "would_sync": payload}

    def sync_dog(self, payload: dict) -> dict:
        return {"synced": False, "reason": "mock", "would_sync": payload}

    def sync_adoption_case(self, payload: dict) -> dict:
        return {"synced": False, "reason": "mock", "would_sync": payload}

    def push_status_update(self, entity: str, entity_id: int, status: str) -> dict:
        return {"synced": False, "reason": "mock", "entity": entity, "id": entity_id, "status": status}


def get_monday_adapter() -> MondayAdapter:
    if settings.monday_api_token:
        pass  # return RealMondayAdapter(settings.monday_api_token)
    return MockMondayAdapter()
