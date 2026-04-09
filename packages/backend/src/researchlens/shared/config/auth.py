from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    access_token_secret: str = "dev-access-secret-change-me"
    refresh_token_secret: str = "dev-refresh-secret-change-me"
    access_token_ttl_minutes: int = Field(default=15, ge=1)
    refresh_token_ttl_minutes: int = Field(default=60 * 24 * 30, ge=1)
    allow_insecure_dev_tokens: bool = True

    model_config = SettingsConfigDict(
        env_prefix="AUTH_",
        extra="ignore",
    )

