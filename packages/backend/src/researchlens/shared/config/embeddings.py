from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingsSettings(BaseSettings):
    provider: Literal["disabled", "openai", "local"] = "disabled"
    model: str | None = None
    api_key: str | None = None
    cache_enabled: bool = True

    model_config = SettingsConfigDict(
        env_prefix="EMBEDDINGS_",
        extra="ignore",
    )
