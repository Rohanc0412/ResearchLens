from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import researchlens.modules.auth.infrastructure.rows  # noqa: F401
import researchlens.modules.conversations.infrastructure.rows  # noqa: F401
import researchlens.modules.projects.infrastructure.project_row  # noqa: F401
from researchlens.shared.config import get_settings
from researchlens.shared.db import (
    ensure_database_url_path,
    metadata,
    normalize_migration_database_url,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = metadata


def _configured_database_url() -> str:
    settings = get_settings()
    url = normalize_migration_database_url(settings.database.url)
    ensure_database_url_path(url)
    return url


def run_migrations_offline() -> None:
    context.configure(
        url=_configured_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _configured_database_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
