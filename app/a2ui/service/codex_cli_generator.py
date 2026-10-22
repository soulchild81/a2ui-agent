import asyncio
import json
import logging
import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import Any

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

_CODEX_OUTPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "a2ui": {
            "type": "string",
            "description": "A2UI messages wrapped in <a2ui-json> and </a2ui-json> tags.",
        }
    },
    "required": ["a2ui"],
    "additionalProperties": False,
}

_SAFE_ENVIRONMENT_KEYS = (
    "CODEX_HOME",
    "HOME",
    "LANG",
    "LC_ALL",
    "NO_PROXY",
    "PATH",
    "SSL_CERT_DIR",
    "SSL_CERT_FILE",
    "TMPDIR",
)


class CodexCliA2uiGenerator:
    def __init__(self, settings: Settings, catalog_service: CatalogService) -> None:
        self._settings = settings
        self._catalog_service = catalog_service

    async def generate(self, request: GenerationRequest) -> list[A2uiMessage]:
        return (await self.generate_result(request)).messages

    async def generate_result(self, request: GenerationRequest) -> GenerationResult:
        executable = shutil.which(self._settings.codex_cli_executable)
        if executable is None:
            raise ApplicationError(
                code="CODEX_CLI_NOT_FOUND",
                message="로컬 Codex CLI 실행 파일을 찾을 수 없습니다.",
                status_code=503,
            )

        request_started_at = perf_counter()
        prompt = self._prompt(request.query)
        sdk_generation_ms = (perf_counter() - request_started_at) * 1_000
        llm_response_ms = 0.0
        last_error: Exception | None = None
        for attempt in range(1, self._settings.llm_max_attempts + 1):
            try:
                response_started_at = perf_counter()
                try:
                    content = await self._call_codex(executable, prompt)
                finally:
                    llm_response_ms += (perf_counter() - response_started_at) * 1_000
                messages = self._catalog_service.parse_response(content)
                self._catalog_service.validate(messages)
                return GenerationResult(
                    messages=messages,
                    context=GenerationContext(
                        user_query=request.query,
                        llm_request_content=prompt,
                        llm_response_content=content,
                        provider="Local Codex",
                        sdk_generation_ms=round(sdk_generation_ms, 2),
                        llm_response_ms=round(llm_response_ms, 2),
                    ),
                )
            except (A2uiError, OSError, RuntimeError, TypeError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "A2UI Codex generation attempt %s failed: %s",
                    attempt,
                    type(exc).__name__,
                )

        raise ApplicationError(
            code="CODEX_GENERATION_FAILED",
            message="Codex 응답을 유효한 A2UI 메시지로 변환하지 못했습니다.",
            status_code=502,
        ) from last_error

    async def _call_codex(self, executable: str, prompt: str) -> str:
        with TemporaryDirectory(prefix="a2ui-codex-") as temporary_directory:
            working_directory = Path(temporary_directory)
            schema_path = working_directory / "output.schema.json"
            response_path = working_directory / "response.json"
            schema_path.write_text(
                json.dumps(_CODEX_OUTPUT_SCHEMA, ensure_ascii=False), encoding="utf-8"
            )

            command = [
                executable,
                "exec",
                "--ephemeral",
                "--ignore-user-config",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--color",
                "never",
                "--cd",
                str(working_directory),
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(response_path),
            ]
            if self._settings.codex_cli_model:
                command.extend(["--model", self._settings.codex_cli_model])
            command.append("-")

            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._safe_environment(),
            )
            try:
                _, _ = await asyncio.wait_for(
                    process.communicate(prompt.encode("utf-8")),
                    timeout=self._settings.codex_cli_timeout_seconds,
                )
            except TimeoutError as exc:
                process.kill()
                await process.wait()
                raise RuntimeError("codex exec timed out") from exc

            if process.returncode != 0:
                raise RuntimeError(f"codex exec exited with status {process.returncode}")
            if not response_path.is_file():
                raise ValueError("codex exec did not write a final response")

            try:
                response: dict[str, Any] = json.loads(response_path.read_text(encoding="utf-8"))
                return str(response["a2ui"])
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                raise ValueError("codex exec returned an invalid structured response") from exc

    def _prompt(self, query: str) -> str:
        return (
            "Generate a safe declarative UI for the user request. "
            "Do not use tools, inspect files, execute commands, or emit HTML or JavaScript. "
            "Use only the supplied A2UI catalog. "
            "Return a JSON object with exactly one property named 'a2ui'. "
            "Its string value must contain only the generated <a2ui-json> blocks.\n\n"
            f"{self._catalog_service.llm_instruction}\n\n"
            f"User request:\n{query}"
        )

    @staticmethod
    def _safe_environment() -> dict[str, str]:
        return {
            key: value
            for key in _SAFE_ENVIRONMENT_KEYS
            if (value := os.environ.get(key)) is not None
        }
