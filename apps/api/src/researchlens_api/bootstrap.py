import logging
from dataclasses import dataclass

from researchlens.modules.projects.infrastructure import SqlAlchemyProjectsRuntime
from researchlens.shared.config import ResearchLensSettings, get_settings
from researchlens.shared.db import DatabaseRuntime, build_database_runtime
from researchlens.shared.logging import configure_logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ApiBootstrapState:
    settings: ResearchLensSettings
    database: DatabaseRuntime
    projects_runtime: SqlAlchemyProjectsRuntime


def build_api_bootstrap_state() -> ApiBootstrapState:
    settings = get_settings()
    configure_logging(
        service_name="api",
        level=settings.observability.log_level,
        json_logs=settings.observability.json_logs,
    )
    database = build_database_runtime(settings)
    logger.info("api bootstrap ready environment=%s", settings.app.environment)
    return ApiBootstrapState(
        settings=settings,
        database=database,
        projects_runtime=SqlAlchemyProjectsRuntime(database.session_factory),
    )
