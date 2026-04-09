from dataclasses import dataclass

from researchlens.shared.config import ResearchLensSettings, get_settings
from researchlens.shared.db import DatabaseRuntime, build_database_runtime


@dataclass(frozen=True)
class ApiBootstrapState:
    settings: ResearchLensSettings
    database: DatabaseRuntime


def build_api_bootstrap_state() -> ApiBootstrapState:
    settings = get_settings()
    return ApiBootstrapState(settings=settings, database=build_database_runtime(settings))
