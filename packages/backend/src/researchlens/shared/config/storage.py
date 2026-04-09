from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageSettings(BaseSettings):
    mode: Literal["local", "s3"] = "local"
    local_artifact_root: Path = Path(".data/artifacts")
    bucket: str | None = None
    endpoint: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="STORAGE_",
        extra="ignore",
    )

