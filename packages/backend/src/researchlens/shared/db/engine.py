from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from researchlens.shared.config.settings_types import ResearchLensSettings


def ensure_database_url_path(url: str) -> None:
    sqlite_prefixes = ("sqlite:///", "sqlite+aiosqlite:///")
    if not url.startswith(sqlite_prefixes):
        return

    raw_path = url.split("///", maxsplit=1)[1]
    database_path = Path(raw_path)
    if database_path.parent != Path():
        database_path.parent.mkdir(parents=True, exist_ok=True)


def normalize_async_database_url(url: str) -> str:
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
    return url


def normalize_migration_database_url(url: str) -> str:
    if url.startswith("sqlite+aiosqlite:///"):
        return url.replace("sqlite+aiosqlite:///", "sqlite:///", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return url


def create_async_engine_from_settings(settings: ResearchLensSettings) -> AsyncEngine:
    normalized_url = normalize_async_database_url(settings.database.url)
    ensure_database_url_path(normalized_url)
    engine_kwargs: dict[str, object] = {
        "echo": settings.database.echo,
        "pool_pre_ping": settings.database.pool_pre_ping,
    }
    if not normalized_url.startswith("sqlite+aiosqlite:///"):
        engine_kwargs["pool_size"] = settings.database.pool_size
        engine_kwargs["max_overflow"] = settings.database.max_overflow
    return create_async_engine(
        normalized_url,
        **engine_kwargs,
    )


def create_sync_engine_from_settings(settings: ResearchLensSettings) -> Engine:
    normalized_url = normalize_migration_database_url(settings.database.url)
    ensure_database_url_path(normalized_url)
    return create_engine(
        normalized_url,
        echo=settings.database.echo,
        pool_pre_ping=settings.database.pool_pre_ping,
    )
