from fastapi import FastAPI
from fastapi.routing import APIRouter
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

from researchlens.modules.auth.presentation import router as auth_router
from researchlens.modules.conversations.presentation import (
    conversation_router,
    message_router,
    run_trigger_router,
)
from researchlens.modules.projects.presentation import router as projects_router
from researchlens.shared.errors import InfrastructureError
from researchlens.shared.logging import RequestLoggingMiddleware
from researchlens_api.bootstrap import build_api_bootstrap_state
from researchlens_api.exception_handlers import register_exception_handlers
from researchlens_api.lifespan import lifespan


def create_app() -> FastAPI:
    state = build_api_bootstrap_state()
    settings = state.settings
    app = FastAPI(
        title=settings.observability.service_name,
        version=settings.app.phase,
        lifespan=lifespan,
    )
    app.state.bootstrap = state
    app.add_middleware(RequestLoggingMiddleware)
    register_exception_handlers(app)

    base_router = APIRouter()

    @base_router.get("/healthz", tags=["bootstrap"])
    def healthz() -> dict[str, str]:
        return {
            "status": "ok",
            "phase": settings.app.phase,
            "service": settings.observability.service_name,
            "environment": settings.app.environment,
        }

    @base_router.get("/health", tags=["bootstrap"])
    async def health() -> dict[str, str]:
        engine = app.state.bootstrap.database.engine
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
                schema_ready = await connection.run_sync(_schema_is_ready)
        except Exception as exc:
            raise InfrastructureError("Database is unavailable.") from exc

        if not schema_ready:
            raise InfrastructureError("Database schema is missing or not migrated.")

        return {"status": "ok"}

    app.include_router(base_router)
    app.include_router(auth_router)
    app.include_router(projects_router)
    app.include_router(conversation_router)
    app.include_router(message_router)
    app.include_router(run_trigger_router)
    return app


def _schema_is_ready(connection: Connection) -> bool:
    inspector = inspect(connection)
    required_tables = {
        "alembic_version",
        "auth_mfa_factors",
        "auth_password_resets",
        "auth_refresh_tokens",
        "auth_sessions",
        "auth_users",
        "conversation_run_triggers",
        "conversations",
        "messages",
        "projects",
    }
    return all(inspector.has_table(table_name) for table_name in required_tables)
