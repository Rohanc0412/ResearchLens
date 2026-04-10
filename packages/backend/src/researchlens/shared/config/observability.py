from pydantic_settings import BaseSettings, SettingsConfigDict


class ObservabilitySettings(BaseSettings):
    service_name: str = "researchlens"
    log_level: str = "INFO"
    json_logs: bool = False
    tracing_enabled: bool = False

    model_config = SettingsConfigDict(
        env_prefix="OBSERVABILITY_",
        extra="ignore",
    )
