from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingsSettings(BaseSettings):
    provider: Literal["disabled", "openai", "local"] = "disabled"
    model: str = "text-embedding-3-small"
    api_key: str | None = None
    base_url: str | None = None
    cache_enabled: bool = True
    batch_size: int = Field(default=64, gt=0)
    max_concurrent_batches: int = Field(default=4, gt=0)
    timeout_seconds: float = Field(default=30.0, gt=0)

    model_config = SettingsConfigDict(
        env_prefix="EMBEDDINGS_",
        extra="ignore",
    )
