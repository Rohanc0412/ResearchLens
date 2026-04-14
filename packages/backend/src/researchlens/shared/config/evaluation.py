from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EvaluationSettings(BaseSettings):
    enabled: bool = True
    max_concurrent_sections: int = Field(default=3, ge=1)
    max_claims_per_section: int = Field(default=24, ge=1)
    stage_timeout_seconds: float = Field(default=180.0, gt=0)
    structured_output_retry_count: int = Field(default=2, ge=0)
    repair_threshold_pct: float = Field(default=70.0, ge=0.0, le=100.0)
    max_repairs_per_section: int = Field(default=1, ge=1)
    section_max_output_tokens: int = Field(default=15000, ge=100)

    model_config = SettingsConfigDict(
        env_prefix="EVALUATION_",
        extra="ignore",
    )
