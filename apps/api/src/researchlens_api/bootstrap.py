import logging
from dataclasses import dataclass

from researchlens.modules.artifacts.infrastructure import SqlAlchemyArtifactsRuntime
from researchlens.modules.auth.infrastructure import SqlAlchemyAuthRuntime
from researchlens.modules.conversations.infrastructure import SqlAlchemyConversationsRuntime
from researchlens.modules.evaluation.infrastructure import SqlAlchemyEvaluationRuntime
from researchlens.modules.evidence.infrastructure import SqlAlchemyEvidenceRuntime
from researchlens.modules.projects.infrastructure import SqlAlchemyProjectsRuntime
from researchlens.modules.repair.infrastructure import SqlAlchemyRepairRuntime
from researchlens.modules.runs.infrastructure import SqlAlchemyRunsRuntime
from researchlens.shared.config import ResearchLensSettings, get_settings
from researchlens.shared.db import DatabaseRuntime, build_database_runtime
from researchlens.shared.logging import configure_logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ApiBootstrapState:
    settings: ResearchLensSettings
    database: DatabaseRuntime
    auth_runtime: SqlAlchemyAuthRuntime
    artifacts_runtime: SqlAlchemyArtifactsRuntime
    conversations_runtime: SqlAlchemyConversationsRuntime
    evidence_runtime: SqlAlchemyEvidenceRuntime
    evaluation_runtime: SqlAlchemyEvaluationRuntime
    projects_runtime: SqlAlchemyProjectsRuntime
    repair_runtime: SqlAlchemyRepairRuntime
    runs_runtime: SqlAlchemyRunsRuntime


def build_api_bootstrap_state() -> ApiBootstrapState:
    settings = get_settings()
    configure_logging(
        service_name="api",
        level=settings.observability.log_level,
        json_logs=settings.observability.json_logs,
    )
    if settings.app.environment != "production" and settings.auth.refresh_cookie_secure:
        logger.warning(
            "local browser auth may fail because AUTH_REFRESH_COOKIE_SECURE=true in %s",
            settings.app.environment,
        )
    database = build_database_runtime(settings)
    logger.info("api bootstrap ready environment=%s", settings.app.environment)
    return ApiBootstrapState(
        settings=settings,
        database=database,
        auth_runtime=SqlAlchemyAuthRuntime(
            session_factory=database.session_factory,
            settings=settings,
        ),
        artifacts_runtime=SqlAlchemyArtifactsRuntime(database.session_factory, settings),
        conversations_runtime=SqlAlchemyConversationsRuntime(database.session_factory),
        evidence_runtime=SqlAlchemyEvidenceRuntime(database.session_factory),
        evaluation_runtime=SqlAlchemyEvaluationRuntime(database.session_factory),
        projects_runtime=SqlAlchemyProjectsRuntime(database.session_factory),
        repair_runtime=SqlAlchemyRepairRuntime(database.session_factory),
        runs_runtime=SqlAlchemyRunsRuntime(database.session_factory, settings),
    )
