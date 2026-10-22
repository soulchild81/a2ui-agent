import asyncio
import json
from pathlib import Path

import pytest

from app.a2ui.domain import GenerationRequest
from app.a2ui.service.catalog_service import CatalogService
from app.a2ui.service.codex_cli_generator import CodexCliA2uiGenerator
from app.a2ui.service.mock_generator import MockA2uiGenerator
from app.common.config import Settings
from app.common.error import ApplicationError


class _SuccessfulProcess:
    returncode = 0

    async def communicate(self, input: bytes) -> tuple[bytes, bytes]:
        return b"", b""

    def kill(self) -> None:
        return None

    async def wait(self) -> int:
        return self.returncode


@pytest.mark.asyncio
async def test_generate_with_codex_cli_returns_valid_a2ui_messages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    catalog_service = CatalogService()
    request = GenerationRequest(query="추천 UI", mode="llm")
    expected_messages = await MockA2uiGenerator(catalog_service).generate(request)

    async def create_process(*command: str, **_: object) -> _SuccessfulProcess:
        response_path = Path(command[command.index("--output-last-message") + 1])
        response_path.write_text(
            json.dumps(
                {
                    "a2ui": (
                        "<a2ui-json>"
                        f"{json.dumps(expected_messages, ensure_ascii=False)}"
                        "</a2ui-json>"
                    )
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return _SuccessfulProcess()

    monkeypatch.setattr("shutil.which", lambda _: "/usr/local/bin/codex")
    monkeypatch.setattr(asyncio, "create_subprocess_exec", create_process)
    generator = CodexCliA2uiGenerator(
        Settings(_env_file=None, llm_provider="codex_cli"), catalog_service
    )

    # When
    result = await generator.generate_result(request)

    # Then
    assert result.messages == expected_messages
    assert result.context.user_query == "추천 UI"
    assert result.context.llm_request_content == generator._prompt("추천 UI")
    assert "<a2ui-json>" in result.context.llm_response_content
    assert result.context.provider == "Local Codex"


@pytest.mark.asyncio
async def test_generate_without_codex_cli_raises_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setattr("shutil.which", lambda _: None)
    generator = CodexCliA2uiGenerator(
        Settings(_env_file=None, llm_provider="codex_cli"), CatalogService()
    )
    request = GenerationRequest(query="폼 UI", mode="llm")

    # When
    with pytest.raises(ApplicationError) as raised:
        await generator.generate(request)

    # Then
    assert raised.value.code == "CODEX_CLI_NOT_FOUND"


def test_safe_environment_does_not_forward_llm_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given
    monkeypatch.setenv("LLM_API_KEY", "should-not-be-forwarded")

    # When
    environment = CodexCliA2uiGenerator._safe_environment()

    # Then
    assert "LLM_API_KEY" not in environment
