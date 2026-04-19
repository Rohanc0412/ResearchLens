from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LlmSettings(BaseSettings):
    provider: Literal["disabled", "openai", "anthropic"] = "disabled"
    model: str = "gpt-5-nano"
    api_key: str | None = None
    base_url: str | None = None
    chat_search_model: str | None = Field(default=None, validation_alias="CHAT_SEARCH_MODEL")
    tavily_api_key: str | None = Field(default=None, validation_alias="TAVILY_API_KEY")
    timeout_seconds: float = Field(default=60.0, gt=0)
    max_output_tokens: int = Field(default=15000, gt=0)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    enable_outline_generation: bool = True
    enable_query_planning: bool = True

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        extra="ignore",
    )
