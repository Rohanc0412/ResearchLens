from fastapi import FastAPI

from researchlens.shared.config import get_settings
from researchlens_api.lifespan import lifespan


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.observability.service_name,
        version=settings.app.phase,
        lifespan=lifespan,
    )

    @app.get("/healthz", tags=["bootstrap"])
    async def healthz() -> dict[str, str]:
        return {
            "status": "ok",
            "phase": settings.app.phase,
            "service": settings.observability.service_name,
            "environment": settings.app.environment,
        }

    return app
