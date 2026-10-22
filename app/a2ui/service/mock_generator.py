import json
from time import perf_counter

from app.a2ui.domain import (
    A2uiMessage,
    GenerationContext,
    GenerationRequest,
    GenerationResult,
)
from app.a2ui.service.catalog_service import CatalogService


class MockA2uiGenerator:
    def __init__(self, catalog_service: CatalogService) -> None:
        self._catalog_service = catalog_service

    async def generate(self, request: GenerationRequest) -> list[A2uiMessage]:
        return (await self.generate_result(request)).messages

    async def generate_result(self, request: GenerationRequest) -> GenerationResult:
        request_started_at = perf_counter()
        llm_request_content = (
            "Mock 모드에서는 LLM을 호출하지 않습니다. "
            "A2UI SDK Catalog를 사용하는 Mock Generator가 메시지를 직접 생성합니다."
        )
        sdk_generation_ms = (perf_counter() - request_started_at) * 1_000
        response_started_at = perf_counter()
        surface_id = "recommendation-surface"
        messages: list[A2uiMessage] = [
            {
                "version": "v0.9",
                "createSurface": {
                    "surfaceId": surface_id,
                    "catalogId": self._catalog_service.catalog_id,
                    "theme": {
                        "primaryColor": "#5b5cf0",
                        "agentDisplayName": "A2UI Lab",
                    },
                    "sendDataModel": True,
                },
            },
            {
                "version": "v0.9",
                "updateComponents": {
                    "surfaceId": surface_id,
                    "components": self._components(request.query),
                },
            },
            {
                "version": "v0.9",
                "updateDataModel": {
                    "surfaceId": surface_id,
                    "value": {
                        "query": request.query,
                        "products": [
                            {
                                "id": "soundfit-air",
                                "name": "SoundFit Air",
                                "price": "79,000원",
                                "summary": "가벼운 착용감과 균형 잡힌 음색",
                            },
                            {
                                "id": "quiet-buds",
                                "name": "Quiet Buds Lite",
                                "price": "89,000원",
                                "summary": "출퇴근에 유용한 노이즈 캔슬링",
                            },
                            {
                                "id": "run-beat",
                                "name": "Run Beat Mini",
                                "price": "59,000원",
                                "summary": "운동용 방수와 안정적인 고정감",
                            },
                        ],
                        "actionStatus": "제품을 선택하면 액션이 에이전트로 전달됩니다.",
                    },
                },
            },
        ]
        self._catalog_service.validate(messages)
        response_ms = (perf_counter() - response_started_at) * 1_000
        return GenerationResult(
            messages=messages,
            context=GenerationContext(
                user_query=request.query,
                llm_request_content=llm_request_content,
                llm_response_content=json.dumps(messages, ensure_ascii=False, indent=2),
                provider="Mock Generator",
                sdk_generation_ms=round(sdk_generation_ms, 2),
                llm_response_ms=round(response_ms, 2),
            ),
        )

    @staticmethod
    def _components(query: str) -> list[dict]:
        components: list[dict] = [
            {
                "id": "root",
                "component": "Column",
                "children": [
                    "title",
                    "queryLabel",
                    "card-0",
                    "card-1",
                    "card-2",
                    "actionStatus",
                ],
                "align": "stretch",
            },
            {"id": "title", "component": "Text", "text": "추천 결과", "variant": "h2"},
            {
                "id": "queryLabel",
                "component": "Text",
                "text": f"요청: {query}",
                "variant": "caption",
            },
        ]
        for index in range(3):
            components.extend(
                [
                    {"id": f"card-{index}", "component": "Card", "child": f"body-{index}"},
                    {
                        "id": f"body-{index}",
                        "component": "Column",
                        "children": [
                            f"name-{index}",
                            f"price-{index}",
                            f"summary-{index}",
                            f"button-{index}",
                        ],
                        "align": "stretch",
                    },
                    {
                        "id": f"name-{index}",
                        "component": "Text",
                        "text": {"path": f"/products/{index}/name"},
                        "variant": "h4",
                    },
                    {
                        "id": f"price-{index}",
                        "component": "Text",
                        "text": {"path": f"/products/{index}/price"},
                    },
                    {
                        "id": f"summary-{index}",
                        "component": "Text",
                        "text": {"path": f"/products/{index}/summary"},
                        "variant": "caption",
                    },
                    {
                        "id": f"button-{index}",
                        "component": "Button",
                        "child": f"button-label-{index}",
                        "variant": "primary",
                        "action": {
                            "event": {
                                "name": "select_product",
                                "context": {
                                    "productId": {"path": f"/products/{index}/id"},
                                    "productName": {"path": f"/products/{index}/name"},
                                },
                            }
                        },
                    },
                    {
                        "id": f"button-label-{index}",
                        "component": "Text",
                        "text": "이 제품 선택",
                    },
                ]
            )
        components.append(
            {
                "id": "actionStatus",
                "component": "Text",
                "text": {"path": "/actionStatus"},
                "variant": "caption",
            }
        )
        return components

