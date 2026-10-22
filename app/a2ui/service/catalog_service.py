from functools import cached_property

from a2ui.core.basic_catalog import BasicCatalog
from a2ui.inference_formats import to_message_dicts
from a2ui.parser import A2uiPart
from a2ui.processor import A2uiRequestProcessor
from a2ui.utils import validate_payload

from app.a2ui.catalog import create_cadenza_catalog
from app.a2ui.domain import A2uiMessage, CatalogProfile
from app.common.error import ApplicationError


class CatalogService:
    protocol_version = "0.9"

    def __init__(self, profile: CatalogProfile = "cadenza") -> None:
        self.profile = profile

    @cached_property
    def catalog(self):
        basic_catalog = BasicCatalog(self.protocol_version, locale="ko-KR")
        if self.profile == "basic":
            return basic_catalog
        return create_cadenza_catalog()

    @cached_property
    def processor(self) -> A2uiRequestProcessor:
        return A2uiRequestProcessor([self.catalog])

    @property
    def catalog_id(self) -> str:
        return self.catalog.id

    @property
    def llm_instruction(self) -> str:
        return self.processor.prompt_snippet

    def validate(self, messages: list[A2uiMessage]) -> None:
        validate_payload([self.catalog], messages)

    def parse_response(self, content: str) -> list[A2uiMessage]:
        parts = self.processor.parse_response(content, wrapped=True)
        messages: list[A2uiMessage] = []
        for part in parts:
            if isinstance(part, A2uiPart):
                messages.extend(to_message_dicts(part.a2ui))
        if not messages:
            raise ValueError("LLM response did not contain an A2UI block")
        return messages

    def ensure_renderer_supports(self, capabilities: dict) -> None:
        if not capabilities:
            return
        version_capabilities = capabilities.get("v0.9", {})
        supported_ids = version_capabilities.get("supportedCatalogIds", [])
        if self.catalog_id not in supported_ids:
            raise ApplicationError(
                code="CATALOG_NOT_SUPPORTED",
                message="클라이언트 렌더러가 에이전트의 A2UI 카탈로그를 지원하지 않습니다.",
                status_code=400,
            )

