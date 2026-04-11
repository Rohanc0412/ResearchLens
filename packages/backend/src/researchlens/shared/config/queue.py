from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class QueueSettings(BaseSettings):
    backend: Literal["db", "memory", "redis"] = "db"
    url: str | None = None
    poll_interval_seconds: int = Field(default=5, ge=1)
    lease_seconds: int = Field(default=30, ge=5)
    max_attempts: int = Field(default=5, ge=1)
    batch_size: int = Field(default=1, ge=1, le=20)
    sse_keepalive_seconds: int = Field(default=2, ge=1)
    sse_terminal_grace_seconds: int = Field(default=1, ge=0)
    run_stub_stage_delay_ms: int = Field(default=10, ge=0)

    model_config = SettingsConfigDict(
        env_prefix="QUEUE_",
        extra="ignore",
    )
