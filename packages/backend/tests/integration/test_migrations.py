from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from researchlens.shared.db import normalize_migration_database_url


def test_alembic_upgrade_creates_phase_5_tables(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = f"sqlite:///{(tmp_path / 'migration-check.db').as_posix()}"
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config("packages/backend/alembic.ini")
    config.set_main_option("script_location", "packages/backend/migrations")

    command.upgrade(config, "head")

    engine = create_engine(normalize_migration_database_url(database_url))
    inspector = inspect(engine)
    assert inspector.has_table("projects")
    assert inspector.has_table("auth_users")
    assert inspector.has_table("auth_sessions")
    assert inspector.has_table("auth_refresh_tokens")
    assert inspector.has_table("auth_password_resets")
    assert inspector.has_table("auth_mfa_factors")
    assert inspector.has_table("conversations")
    assert inspector.has_table("messages")
    assert inspector.has_table("conversation_run_triggers")
    assert inspector.has_table("runs")
    assert inspector.has_table("run_events")
    assert inspector.has_table("run_status_transitions")
    assert inspector.has_table("run_checkpoints")
    assert inspector.has_table("run_queue_items")
    assert inspector.has_table("retrieval_sources")
    assert inspector.has_table("retrieval_source_snapshots")
    assert inspector.has_table("retrieval_source_chunks")
    assert inspector.has_table("retrieval_chunk_embeddings")
    assert inspector.has_table("run_retrieval_sources")
    assert inspector.has_table("alembic_version")
