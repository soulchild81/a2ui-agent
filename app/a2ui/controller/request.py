from typing import Any, Literal

from pydantic import BaseModel, Field

MAX_QUERY_LENGTH = 20_000


class GenerateA2uiRequest(BaseModel):
    query: str = Field(min_length=1, max_length=MAX_QUERY_LENGTH)
    mode: Literal["mock", "llm"] | None = None
    llm_provider: Literal["api", "codex_cli"] | None = None
    catalog_profile: Literal["cadenza", "basic"] = "cadenza"
    renderer_capabilities: dict[str, Any] = Field(default_factory=dict)


class A2uiActionRequest(BaseModel):
    name: str
    surfaceId: str
    sourceComponentId: str
    context: dict[str, Any] = Field(default_factory=dict)

