import logging
from dataclasses import dataclass

from researchlens.shared.config import ResearchLensSettings, get_settings
from researchlens.shared.db import DatabaseRuntime, build_database_runtime
from researchlens.shared.logging import configure_logging
from researchlens.worker_composition import WorkerRunsRuntime, build_worker_runs_runtime

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkerBootstrapState:
    settings: ResearchLensSettings
    database: DatabaseRuntime
    runs_runtime: WorkerRunsRuntime


def build_worker_bootstrap_state() -> WorkerBootstrapState:
    settings = get_settings()
    configure_logging(
        service_name="worker",
        level=settings.observability.log_level,
        json_logs=settings.observability.json_logs,
    )
    logger.info("worker bootstrap ready environment=%s", settings.app.environment)
    database = build_database_runtime(settings)
    return WorkerBootstrapState(
        settings=settings,
        database=database,
        runs_runtime=build_worker_runs_runtime(database=database, settings=settings),
    )
