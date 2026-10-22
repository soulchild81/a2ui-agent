import json
import logging
from time import perf_counter
from typing import Any

import httpx
from a2ui.core import A2uiError

from app.a2ui.domain import (
    A2uiMessage,
    GenerationContext,
    GenerationRequest,
    GenerationResult,
)
from app.a2ui.service.catalog_service import CatalogService
from app.common.config import Settings
from app.common.error import ApplicationError

logger = logging.getLogger(__name__)


class LlmA2uiGenerator:
    def __init__(self, settings: Settings, catalog_service: CatalogService) -> None:
        self._settings = settings
        self._catalog_service = catalog_service

    async def generate(self, request: GenerationRequest) -> list[A2uiMessage]:
        return (await self.generate_result(request)).messages

    async def generate_result(self, request: GenerationRequest) -> GenerationResult:
        if not self._settings.llm_api_key or not self._settings.llm_model:
            raise ApplicationError(
                code="LLM_NOT_CONFIGURED",
                message="LLM 모드를 사용하려면 LLM_API_KEY와 LLM_MODEL을 설정해야 합니다.",
                status_code=503,
            )

        request_started_at = perf_counter()
        payload = self._request_payload(request.query)
        sdk_generation_ms = (perf_counter() - request_started_at) * 1_000
        llm_response_ms = 0.0
        last_error: Exception | None = None
        for attempt in range(1, self._settings.llm_max_attempts + 1):
            try:
                response_started_at = perf_counter()
                try:
                    content = await self._call_llm(payload)
                finally:
                    llm_response_ms += (perf_counter() - response_started_at) * 1_000
                messages = self._catalog_service.parse_response(content)
                self._catalog_service.validate(messages)
                return GenerationResult(
                    messages=messages,
                    context=GenerationContext(
                        user_query=request.query,
                        llm_request_content=json.dumps(
                            payload, ensure_ascii=False, indent=2
                        ),
                        llm_response_content=content,
                        provider="Gemini API",
                        sdk_generation_ms=round(sdk_generation_ms, 2),
                        llm_response_ms=round(llm_response_ms, 2),
                    ),
                )
            except (A2uiError, httpx.HTTPError, ValueError, TypeError) as exc:
                last_error = exc
                logger.warning("A2UI LLM generation attempt %s failed: %s", attempt, exc)

        raise ApplicationError(
            code="A2UI_GENERATION_FAILED",
            message="LLM 응답을 유효한 A2UI 메시지로 변환하지 못했습니다.",
            status_code=502,
        ) from last_error

    async def _call_llm(self, payload: dict[str, Any]) -> str:
        endpoint = f"{self._settings.llm_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self._settings.llm_timeout_seconds) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
        body: dict[str, Any] = response.json()
        try:
            return str(body["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("LLM response does not contain message content") from exc

    def _request_payload(self, query: str) -> dict[str, Any]:
        return {
            "model": self._settings.llm_model,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You generate safe declarative UI. Use only the supplied A2UI catalog. "
                        "Never emit HTML or JavaScript.\n\n"
                        + self._catalog_service.llm_instruction
                    ),
                },
                {"role": "user", "content": query},
            ],
        }


