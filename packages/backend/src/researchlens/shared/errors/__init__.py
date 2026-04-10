"""Shared error contracts belong here."""

from researchlens.shared.errors.base import ResearchLensError
from researchlens.shared.errors.http_mapping import error_response, map_error_to_status_code
from researchlens.shared.errors.types import (
    ConflictError,
    InfrastructureError,
    NotFoundError,
    ValidationError,
)

__all__ = [
    "ConflictError",
    "InfrastructureError",
    "NotFoundError",
    "ResearchLensError",
    "ValidationError",
    "error_response",
    "map_error_to_status_code",
]
