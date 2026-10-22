import json
import logging
from collections.abc import AsyncIterator
from dataclasses import asdict
from time import perf_counter
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.a2ui.controller.dependencies import get_generation_service
from app.a2ui.controller.request import A2uiActionRequest, GenerateA2uiRequest
from app.a2ui.controller.response import ActionResponse
from app.a2ui.domain import A2uiAction, GenerationRequest
from app.a2ui.service import A2uiGenerationService
from app.a2ui.service.catalog_service import CatalogService
from app.common.config import get_settings
from app.common.error import ApplicationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/a2ui", tags=["a2ui"])


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.get("/catalogs/{profile}")
async def get_catalog(
    profile: Literal["cadenza", "basic"],
) -> dict:
    return CatalogService(profile).catalog.to_json()


@router.post("/stream", response_class=StreamingResponse)
async def stream_a2ui(
    body: GenerateA2uiRequest,
    service: Annotated[A2uiGenerationService, Depends(get_generation_service)],
) -> StreamingResponse:
    mode = body.mode or get_settings().a2ui_mode
    request = GenerationRequest(
        query=body.query,
        mode=mode,
        llm_provider=body.llm_provider,
        catalog_profile=body.catalog_profile,
        renderer_capabilities=body.renderer_capabilities,
    )

    async def events() -> AsyncIterator[str]:
        generation_started_at = perf_counter()
        try:
            result = await service.generate(request)
            generation_ms = (perf_counter() - generation_started_at) * 1_000
            yield _sse("generation_context", asdict(result.context))
            yield _sse("timing", {"agent_generation_ms": round(generation_ms, 2)})
            for message in result.messages:
                yield _sse("a2ui", message)
            yield _sse("done", {"status": "completed"})
        except ApplicationError as exc:
            logger.info("A2UI stream ended with application error: %s", exc.code)
            yield _sse("error", {"code": exc.code, "message": exc.message})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/actions", response_model=ActionResponse)
async def handle_action(
    body: A2uiActionRequest,
    request: Request,
    service: Annotated[A2uiGenerationService, Depends(get_generation_service)],
) -> ActionResponse:
    action_payload = await request.json()
    logger.info(
        "A2UI action request payload=%s",
        json.dumps(action_payload, ensure_ascii=False, separators=(",", ":")),
    )
    messages = service.handle_action(
        A2uiAction(
            name=body.name,
            surface_id=body.surfaceId,
            source_component_id=body.sourceComponentId,
            context=body.context,
        )
    )
    return ActionResponse(messages=messages)

