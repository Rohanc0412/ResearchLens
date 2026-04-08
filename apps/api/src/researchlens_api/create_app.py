from fastapi import FastAPI

from researchlens_api.bootstrap import ApiBootstrapConfig
from researchlens_api.lifespan import lifespan


def create_app() -> FastAPI:
    config = ApiBootstrapConfig()
    app = FastAPI(title=config.app_name, version=config.phase, lifespan=lifespan)

    @app.get("/healthz", tags=["bootstrap"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "phase": config.phase}

    return app

