"""Database bootstrap helpers for installed-package execution."""

from researchlens.shared.db.base import Base, metadata
from researchlens.shared.db.bootstrap import DatabaseRuntime, build_database_runtime
from researchlens.shared.db.engine import (
    create_async_engine_from_settings,
    create_sync_engine_from_settings,
    ensure_database_url_path,
    normalize_async_database_url,
    normalize_migration_database_url,
)
from researchlens.shared.db.session import build_session_factory, session_scope
from researchlens.shared.db.transaction_manager import (
    SqlAlchemyTransactionManager,
    TransactionManager,
)

__all__ = [
    "Base",
    "DatabaseRuntime",
    "SqlAlchemyTransactionManager",
    "TransactionManager",
    "build_database_runtime",
    "build_session_factory",
    "create_async_engine_from_settings",
    "create_sync_engine_from_settings",
    "ensure_database_url_path",
    "metadata",
    "normalize_async_database_url",
    "normalize_migration_database_url",
    "session_scope",
]
