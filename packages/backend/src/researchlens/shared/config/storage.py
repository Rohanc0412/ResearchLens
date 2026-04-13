from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageSettings(BaseSettings):
    mode: Literal["local"] = "local"
    local_artifact_root: Path = Path(".data/artifacts")

    model_config = SettingsConfigDict(
        env_prefix="STORAGE_",
        extra="ignore",
    )
