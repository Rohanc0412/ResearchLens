from fastapi.responses import JSONResponse

from researchlens.shared.errors.base import ResearchLensError
from researchlens.shared.errors.types import (
    ConflictError,
    InfrastructureError,
    NotFoundError,
    ValidationError,
)


def map_error_to_status_code(error: ResearchLensError) -> int:
    if isinstance(error, ValidationError):
        return 422
    if isinstance(error, ConflictError):
        return 409
    if isinstance(error, NotFoundError):
        return 404
    if isinstance(error, InfrastructureError):
        return 503
    return 500


def error_response(error: ResearchLensError) -> JSONResponse:
    return JSONResponse(
        status_code=map_error_to_status_code(error),
        content={
            "detail": error.message,
            "code": error.code,
        },
    )
