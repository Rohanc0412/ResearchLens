from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    required: bool = True
    dev_bypass_auth: bool = False
    access_token_secret: str = "dev-access-secret-change-me-32-bytes"
    refresh_token_secret: str = "dev-refresh-secret-change-me"
    password_reset_token_secret: str = "dev-password-reset-secret-change-me"
    jwt_issuer: str = "researchlens"
    access_token_ttl_minutes: int = Field(default=15, ge=1)
    refresh_token_ttl_days: int = Field(default=30, ge=1)
    refresh_cookie_name: str = "researchlens_refresh"
    refresh_cookie_secure: bool = False
    refresh_cookie_samesite: str = "lax"
    allow_register: bool = True
    clock_skew_seconds: int = Field(default=30, ge=0)
    mfa_challenge_minutes: int = Field(default=5, ge=1)
    mfa_totp_issuer: str = "ResearchLens"
    mfa_totp_period_seconds: int = Field(default=30, ge=1)
    mfa_totp_digits: int = Field(default=6, ge=6, le=8)
    mfa_totp_window: int = Field(default=1, ge=0)
    password_reset_minutes: int = Field(default=30, ge=1)
    allow_insecure_dev_tokens: bool = True

    model_config = SettingsConfigDict(
        env_prefix="AUTH_",
        extra="ignore",
    )
