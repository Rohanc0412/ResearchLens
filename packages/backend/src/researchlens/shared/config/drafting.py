from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DraftingSettings(BaseSettings):
    enabled: bool = True
    max_sections_per_run: int = Field(default=8, ge=1)
    max_evidence_items_per_section: int = Field(default=6, ge=1)
    max_evidence_chars_per_item: int = Field(default=900, ge=100)
    section_min_words: int = Field(default=120, ge=1)
    section_max_words: int = Field(default=260, ge=1)
    section_max_output_tokens: int = Field(default=15000, ge=100)
    correction_retry_count: int = Field(default=2, ge=0)
    max_concurrent_section_preparation: int = Field(default=4, ge=1)
    max_concurrent_section_drafts: int = Field(default=3, ge=1)
    max_concurrent_section_persistence: int = Field(default=4, ge=1)
    stage_timeout_seconds: float = Field(default=180.0, gt=0)

    model_config = SettingsConfigDict(
        env_prefix="DRAFTING_",
        extra="ignore",
    )
