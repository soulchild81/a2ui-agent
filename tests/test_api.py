import json

from fastapi.testclient import TestClient

from app.a2ui.controller.dependencies import get_generation_service
from app.a2ui.service import A2uiGenerationService
from app.a2ui.service.catalog_service import CatalogService
from app.common.config import Settings
from app.main import app

client = TestClient(app)


def _sse_payloads(response_text: str, event_name: str) -> list[dict]:
    payloads: list[dict] = []
    blocks = response_text.strip().split("\n\n")
    for block in blocks:
        lines = block.splitlines()
        if f"event: {event_name}" not in lines:
            continue
        data_line = next(line for line in lines if line.startswith("data: "))
        payloads.append(json.loads(data_line.removeprefix("data: ")))
    return payloads


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "mock", "protocol_version": "v0.9"}


def test_stream_returns_valid_a2ui_sequence() -> None:
    response = client.post(
        "/api/v1/a2ui/stream",
        json={"query": "10만 원 이하 무선 이어폰 추천", "mode": "mock"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    messages = _sse_payloads(response.text, "a2ui")
    assert len(messages) == 3
    assert messages[0]["createSurface"]["surfaceId"] == "recommendation-surface"
    assert messages[1]["updateComponents"]["components"][0]["id"] == "root"
    assert messages[2]["updateDataModel"]["value"]["products"][0]["price"] == "79,000원"


def test_stream_returns_agent_generation_timing() -> None:
    # Given / When
    response = client.post(
        "/api/v1/a2ui/stream",
        json={"query": "응답 시간 측정", "mode": "mock"},
    )

    # Then
    timings = _sse_payloads(response.text, "timing")
    assert isinstance(timings[0]["agent_generation_ms"], float)


def test_stream_returns_generation_context_without_secrets() -> None:
    response = client.post(
        "/api/v1/a2ui/stream",
        json={"query": "추천 UI", "mode": "mock"},
    )

    contexts = _sse_payloads(response.text, "generation_context")
    assert len(contexts) == 1
    context = contexts[0]
    assert context["user_query"] == "추천 UI"
    assert context["llm_request_content"].startswith("Mock 모드에서는 LLM을 호출하지 않습니다.")
    assert '"createSurface"' in context["llm_response_content"]
    assert context["provider"] == "Mock Generator"
    assert isinstance(context["sdk_generation_ms"], float)
    assert isinstance(context["llm_response_ms"], float)


def test_action_updates_surface_data_model() -> None:
    response = client.post(
        "/api/v1/a2ui/actions",
        json={
            "name": "select_product",
            "surfaceId": "recommendation-surface",
            "sourceComponentId": "button-0",
            "context": {"productName": "SoundFit Air"},
        },
    )

    assert response.status_code == 200
    update = response.json()["messages"][0]["updateDataModel"]
    assert update["path"] == "/actionStatus"
    assert "SoundFit Air" in update["value"]


def test_llm_mode_reports_configuration_error_as_sse() -> None:
    settings = Settings(
        _env_file=None,
        llm_provider="codex_cli",
        llm_api_key="",
        llm_model="",
    )
    service = A2uiGenerationService(settings, CatalogService())
    app.dependency_overrides[get_generation_service] = lambda: service
    try:
        response = client.post(
            "/api/v1/a2ui/stream",
            json={
                "query": "폼을 만들어줘",
                "mode": "llm",
                "llm_provider": "api",
            },
        )
    finally:
        app.dependency_overrides.pop(get_generation_service, None)

    errors = _sse_payloads(response.text, "error")
    assert errors == [
        {
            "code": "LLM_NOT_CONFIGURED",
            "message": "LLM 모드를 사용하려면 LLM_API_KEY와 LLM_MODEL을 설정해야 합니다.",
        }
    ]


def test_stream_rejects_unknown_renderer_catalog() -> None:
    response = client.post(
        "/api/v1/a2ui/stream",
        json={
            "query": "추천 UI",
            "mode": "mock",
            "renderer_capabilities": {
                "v0.9": {"supportedCatalogIds": ["https://example.com/unknown.json"]}
            },
        },
    )

    errors = _sse_payloads(response.text, "error")
    assert errors[0]["code"] == "CATALOG_NOT_SUPPORTED"


def test_catalog_allows_only_composer_mapped_components() -> None:
    catalog_service = CatalogService()

    assert set(catalog_service.catalog.components) == {
        "Text",
        "Row",
        "Column",
        "Card",
        "Button",
    }


def test_basic_catalog_exposes_more_components_than_cadenza_profile() -> None:
    cadenza_catalog = CatalogService("cadenza").catalog
    basic_catalog = CatalogService("basic").catalog

    assert len(basic_catalog.components) > len(cadenza_catalog.components)

