from collections.abc import AsyncIterator

from app.a2ui.domain import (
    A2uiAction,
    A2uiMessage,
    GenerationRequest,
    GenerationResult,
)
from app.a2ui.service.catalog_service import CatalogService
from app.a2ui.service.codex_cli_generator import CodexCliA2uiGenerator
from app.a2ui.service.llm_generator import LlmA2uiGenerator
from app.a2ui.service.mock_generator import MockA2uiGenerator
from app.common.config import Settings


class A2uiGenerationService:
    def __init__(self, settings: Settings, catalog_service: CatalogService) -> None:
        self._catalog_service = catalog_service
        self._default_llm_provider = settings.llm_provider
        self._catalog_services = {
            "cadenza": catalog_service,
            "basic": CatalogService("basic"),
        }
        self._mock_generators = {
            profile: MockA2uiGenerator(service)
            for profile, service in self._catalog_services.items()
        }
        self._llm_generators = {
            profile: {
                "api": LlmA2uiGenerator(settings, service),
                "codex_cli": CodexCliA2uiGenerator(settings, service),
            }
            for profile, service in self._catalog_services.items()
        }

    async def stream(self, request: GenerationRequest) -> AsyncIterator[A2uiMessage]:
        result = await self.generate(request)
        for message in result.messages:
            yield message

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        catalog_service = self._catalog_services[request.catalog_profile]
        catalog_service.ensure_renderer_supports(request.renderer_capabilities)
        generator = self._select_generator(request)
        return await generator.generate_result(request)

    def _select_generator(self, request: GenerationRequest):
        if request.mode == "mock":
            return self._mock_generators[request.catalog_profile]
        provider = request.llm_provider or self._default_llm_provider
        return self._llm_generators[request.catalog_profile][provider]

    def handle_action(self, action: A2uiAction) -> list[A2uiMessage]:
        product_name = str(action.context.get("productName", "선택한 제품"))
        messages: list[A2uiMessage] = [
            {
                "version": "v0.9",
                "updateDataModel": {
                    "surfaceId": action.surface_id,
                    "path": "/actionStatus",
                    "value": f"'{product_name}' 선택 액션을 에이전트가 처리했습니다.",
                },
            }
        ]
        self._catalog_service.validate(messages)
        return messages

