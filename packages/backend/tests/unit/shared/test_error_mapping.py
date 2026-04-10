from researchlens.shared.errors import (
    ConflictError,
    InfrastructureError,
    NotFoundError,
    ValidationError,
    map_error_to_status_code,
)


def test_map_error_to_status_code() -> None:
    assert map_error_to_status_code(ValidationError()) == 422
    assert map_error_to_status_code(ConflictError()) == 409
    assert map_error_to_status_code(NotFoundError()) == 404
    assert map_error_to_status_code(InfrastructureError()) == 503
