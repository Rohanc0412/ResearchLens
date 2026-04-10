from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict


class BootstrapActorSettings(BaseSettings):
    enabled: bool = True
    tenant_id: UUID = UUID("00000000-0000-0000-0000-000000000001")
    user_id: str = "bootstrap-user"

    model_config = SettingsConfigDict(
        env_prefix="BOOTSTRAP_ACTOR_",
        extra="ignore",
    )
