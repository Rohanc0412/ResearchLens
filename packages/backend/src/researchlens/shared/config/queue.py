from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class QueueSettings(BaseSettings):
    backend: Literal["memory", "redis"] = "memory"
    url: str | None = None
    poll_interval_seconds: int = Field(default=5, ge=1)

    model_config = SettingsConfigDict(
        env_prefix="QUEUE_",
        extra="ignore",
    )

