from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RetrievalSettings(BaseSettings):
    enabled: bool = False
    max_sources_per_run: int = Field(default=20, ge=1)
    allow_external_fetch: bool = False

    model_config = SettingsConfigDict(
        env_prefix="RETRIEVAL_",
        extra="ignore",
    )

