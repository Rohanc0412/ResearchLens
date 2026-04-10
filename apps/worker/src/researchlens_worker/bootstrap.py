import logging
from dataclasses import dataclass

from researchlens.shared.config import ResearchLensSettings, get_settings
from researchlens.shared.db import DatabaseRuntime, build_database_runtime
from researchlens.shared.logging import configure_logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkerBootstrapState:
    settings: ResearchLensSettings
    database: DatabaseRuntime


def build_worker_bootstrap_state() -> WorkerBootstrapState:
    settings = get_settings()
    configure_logging(
        service_name="worker",
        level=settings.observability.log_level,
        json_logs=settings.observability.json_logs,
    )
    logger.info("worker bootstrap ready environment=%s", settings.app.environment)
    return WorkerBootstrapState(settings=settings, database=build_database_runtime(settings))
