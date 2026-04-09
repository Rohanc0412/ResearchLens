from dataclasses import dataclass

from researchlens.shared.config import ResearchLensSettings, get_settings
from researchlens.shared.db import DatabaseRuntime, build_database_runtime


@dataclass(frozen=True)
class WorkerBootstrapState:
    settings: ResearchLensSettings
    database: DatabaseRuntime


def build_worker_bootstrap_state() -> WorkerBootstrapState:
    settings = get_settings()
    return WorkerBootstrapState(settings=settings, database=build_database_runtime(settings))
