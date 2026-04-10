from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from researchlens.shared.config import get_settings, reset_settings_cache
from researchlens.shared.db import DatabaseRuntime, build_database_runtime


@pytest.fixture(autouse=True)
def reset_settings() -> Generator[None, None, None]:
    reset_settings_cache()
    yield
    reset_settings_cache()


def _alembic_config() -> Config:
    config = Config("packages/backend/alembic.ini")
    config.set_main_option("script_location", "packages/backend/migrations")
    return config


@pytest.fixture
def sqlite_database_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    database_path = tmp_path / "researchlens-test.db"
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", database_url)
    return database_url


@pytest.fixture
def migrated_database_url(sqlite_database_url: str) -> str:
    command.upgrade(_alembic_config(), "head")
    return sqlite_database_url


@pytest.fixture
async def database_runtime(
    migrated_database_url: str,
) -> Generator[DatabaseRuntime, None, None]:
    runtime = build_database_runtime(get_settings())
    try:
        yield runtime
    finally:
        await runtime.dispose()
