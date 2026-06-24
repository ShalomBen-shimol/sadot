from pydantic import BaseModel


class StatusTransition(BaseModel):
    """Generic status-change request for workflow entities."""
    status: str
    note: str | None = None


class Message(BaseModel):
    detail: str
