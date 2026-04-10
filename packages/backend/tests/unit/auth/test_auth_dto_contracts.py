import pytest
from pydantic import ValidationError as PydanticValidationError

from researchlens.modules.auth.presentation.request_models import LoginRequestDto
from researchlens.modules.auth.presentation.response_models import (
    AuthenticatedUserDto,
    AuthTokenResponseDto,
    LogoutResponseDto,
    PasswordResetConfirmResponseDto,
    PasswordResetRequestResponseDto,
)


def test_request_dto_forbids_extra_fields() -> None:
    with pytest.raises(PydanticValidationError):
        LoginRequestDto.model_validate(
            {"identifier": "casey", "password": "CorrectHorse1!", "unexpected": True}
        )


def test_public_response_dtos_forbid_extra_fields() -> None:
    user = AuthenticatedUserDto(
        user_id="11111111-1111-1111-1111-111111111111",
        username="casey",
        email="casey@example.com",
        tenant_id="22222222-2222-2222-2222-222222222222",
        roles=["owner"],
    )

    with pytest.raises(PydanticValidationError):
        AuthTokenResponseDto.model_validate(
            {
                "access_token": "token",
                "expires_in": 900,
                "user": user,
                "unexpected": True,
            }
        )


def test_status_response_shapes_are_strict() -> None:
    assert LogoutResponseDto().model_dump() == {"status": "ok"}
    assert PasswordResetRequestResponseDto().model_dump() == {"status": "ok"}
    assert PasswordResetConfirmResponseDto().model_dump() == {"status": "ok"}
