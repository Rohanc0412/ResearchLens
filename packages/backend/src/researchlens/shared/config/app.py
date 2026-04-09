from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    environment: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = False
    phase: str = "phase-1"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    worker_name: str = "researchlens-worker"

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        extra="ignore",
    )

