import json
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class AppSettings(BaseSettings):
    environment: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = False
    phase: str = "phase-8"
    api_host: str = "localhost"
    api_port: int = 8017
    worker_name: str = "researchlens-worker"
    cors_allowed_origins: Annotated[tuple[str, ...], NoDecode] = Field(
        default=("http://localhost:4273",)
    )

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _parse_cors_allowed_origins(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return ()
            if stripped.startswith("["):
                parsed = json.loads(stripped)
                if not isinstance(parsed, list):
                    raise ValueError("APP_CORS_ALLOWED_ORIGINS must be a JSON list or CSV string.")
                return parsed
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        extra="ignore",
    )
