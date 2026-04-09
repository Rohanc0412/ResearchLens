from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class LlmSettings(BaseSettings):
    provider: Literal["disabled", "openai", "anthropic"] = "disabled"
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        extra="ignore",
    )

