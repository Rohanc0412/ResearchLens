import pytest
from pydantic import ValidationError as PydanticValidationError

from researchlens.modules.auth.presentation.request_models import (
    LoginRequestDto,
    MfaChallengeVerifyRequestDto,
    MfaDisableRequestDto,
    MfaEnrollVerifyRequestDto,
)
from researchlens.modules.auth.presentation.response_models import (
    AuthenticatedUserDto,
    AuthTokenResponseDto,
    LogoutResponseDto,
    MfaEnabledResponseDto,
    MfaEnrollStartResponseDto,
    MfaStatusResponseDto,
    PasswordResetConfirmResponseDto,
    PasswordResetRequestResponseDto,
)


def test_request_dto_forbids_extra_fields() -> None:
    with pytest.raises(PydanticValidationError):
        LoginRequestDto.model_validate(
            {"identifier": "casey", "password": "CorrectHorse1!", "unexpected": True}
        )
    with pytest.raises(PydanticValidationError):
        MfaEnrollVerifyRequestDto.model_validate({"code": "123456", "unexpected": True})
    with pytest.raises(PydanticValidationError):
        MfaChallengeVerifyRequestDto.model_validate(
            {"mfa_token": "token", "code": "123456", "unexpected": True}
        )
    with pytest.raises(PydanticValidationError):
        MfaDisableRequestDto.model_validate({"code": "123456", "unexpected": True})


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
    assert MfaStatusResponseDto(enabled=True, pending=False).model_dump() == {
        "enabled": True,
        "pending": False,
    }
    assert MfaEnabledResponseDto(enabled=False).model_dump() == {"enabled": False}


def test_mfa_enroll_response_shape_is_strict() -> None:
    response = MfaEnrollStartResponseDto(
        secret="secret",
        otpauth_uri="otpauth://totp/example",
        issuer="ResearchLens",
        account_name="casey@example.com",
        period=30,
        digits=6,
    )

    assert set(response.model_dump()) == {
        "secret",
        "otpauth_uri",
        "issuer",
        "account_name",
        "period",
        "digits",
    }
    with pytest.raises(PydanticValidationError):
        MfaEnrollStartResponseDto.model_validate(
            {
                "secret": "secret",
                "otpauth_uri": "otpauth://totp/example",
                "issuer": "ResearchLens",
                "account_name": "casey@example.com",
                "period": 30,
                "digits": 6,
                "unexpected": True,
            }
        )
