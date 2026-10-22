from typing import Any

from pydantic import BaseModel


class ActionResponse(BaseModel):
    messages: list[dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    mode: str
    protocol_version: str

