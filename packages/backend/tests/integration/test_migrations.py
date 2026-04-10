from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from researchlens.shared.db import normalize_migration_database_url


def test_alembic_upgrade_creates_projects_table(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'migration-check.db').as_posix()}"
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config("packages/backend/alembic.ini")
    config.set_main_option("script_location", "packages/backend/migrations")

    command.upgrade(config, "head")

    engine = create_engine(normalize_migration_database_url(database_url))
    inspector = inspect(engine)
    assert inspector.has_table("projects")
    assert inspector.has_table("alembic_version")
