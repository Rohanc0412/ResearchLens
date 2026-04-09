from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchlens.shared.config.settings_types import ResearchLensSettings
from researchlens.shared.db.engine import create_async_engine_from_settings


def build_session_factory(
    settings: ResearchLensSettings,
) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine_from_settings(settings)
    return async_sessionmaker(bind=engine, expire_on_commit=False)
