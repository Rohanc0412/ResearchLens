import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from researchlens.shared.errors import ResearchLensError, error_response

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ResearchLensError)
    def handle_known_error(
        request: Request,
        exc: ResearchLensError,
    ) -> JSONResponse:
        logger.warning("request failed code=%s path=%s", exc.code, request.url.path)
        return error_response(exc)

    @app.exception_handler(Exception)
    def handle_unexpected_error(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("unexpected server error path=%s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error.",
                "code": "internal_error",
            },
        )
