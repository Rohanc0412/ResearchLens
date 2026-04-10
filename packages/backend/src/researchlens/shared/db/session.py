from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from researchlens.shared.config.settings_types import ResearchLensSettings
from researchlens.shared.db.engine import create_async_engine_from_settings


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )


def build_session_factory(
    settings: ResearchLensSettings,
) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine_from_settings(settings)
    return create_session_factory(engine)


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
