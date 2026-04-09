from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    url: str = "sqlite+aiosqlite:///./.data/researchlens.db"
    echo: bool = False
    pool_size: int = Field(default=5, ge=1)
    max_overflow: int = Field(default=10, ge=0)
    pool_pre_ping: bool = True
    run_migrations_on_startup: bool = False

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        extra="ignore",
    )

