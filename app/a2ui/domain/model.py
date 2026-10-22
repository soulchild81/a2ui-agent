from dataclasses import dataclass, field
from typing import Any, Literal

type A2uiMessage = dict[str, Any]
type LlmProvider = Literal["api", "codex_cli"]
type CatalogProfile = Literal["cadenza", "basic"]


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    query: str
    mode: Literal["mock", "llm"]
    llm_provider: LlmProvider | None = None
    catalog_profile: CatalogProfile = "cadenza"
    renderer_capabilities: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GenerationContext:
    user_query: str
    llm_request_content: str
    llm_response_content: str
    provider: str
    sdk_generation_ms: float
    llm_response_ms: float


@dataclass(frozen=True, slots=True)
class GenerationResult:
    messages: list[A2uiMessage]
    context: GenerationContext


@dataclass(frozen=True, slots=True)
class A2uiAction:
    name: str
    surface_id: str
    source_component_id: str
    context: dict[str, Any] = field(default_factory=dict)

