from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from researchlens.shared.config.settings_types import ResearchLensSettings
from researchlens.shared.db.engine import create_async_engine_from_settings
from researchlens.shared.db.model_registry import register_db_models
from researchlens.shared.db.session import create_session_factory


@dataclass(frozen=True)
class DatabaseRuntime:
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]

    async def dispose(self) -> None:
        await self.engine.dispose()


def build_database_runtime(settings: ResearchLensSettings) -> DatabaseRuntime:
    register_db_models()
    engine = create_async_engine_from_settings(settings)
    session_factory = create_session_factory(engine)
    return DatabaseRuntime(engine=engine, session_factory=session_factory)
