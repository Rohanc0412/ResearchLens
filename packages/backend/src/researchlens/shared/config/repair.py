from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RepairSettings(BaseSettings):
    enabled: bool = True
    max_concurrent_sections: int = Field(default=2, ge=1)
    stage_timeout_seconds: float = Field(default=180.0, gt=0)
    section_max_output_tokens: int = Field(default=15000, ge=100)

    model_config = SettingsConfigDict(
        env_prefix="REPAIR_",
        extra="ignore",
    )
