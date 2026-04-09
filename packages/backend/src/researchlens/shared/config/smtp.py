from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SmtpSettings(BaseSettings):
    enabled: bool = False
    host: str | None = None
    port: int = Field(default=587, ge=1, le=65535)
    username: str | None = None
    password: str | None = None
    starttls: bool = True
    from_name: str = "ResearchLens"
    from_email: EmailStr = "noreply@example.com"

    model_config = SettingsConfigDict(
        env_prefix="SMTP_",
        extra="ignore",
    )
