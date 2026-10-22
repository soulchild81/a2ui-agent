from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "A2UI Lab Agent"
    a2ui_mode: Literal["mock", "llm"] = "mock"
    a2ui_cors_origins: list[str] = Field(
        default_factory=lambda: ["http://127.0.0.1:5173", "http://localhost:5173"]
    )
    llm_provider: Literal["api", "codex_cli"] = "api"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = ""
    llm_api_key: str = ""
    llm_timeout_seconds: float = 30.0
    llm_max_attempts: int = 2
    codex_cli_executable: str = "codex"
    codex_cli_model: str = ""
    codex_cli_timeout_seconds: float = 120.0


@lru_cache
def get_settings() -> Settings:
    return Settings()

