"""Auth application layer placeholder."""

from researchlens.modules.auth.application.confirm_password_reset import (
    ConfirmPasswordResetCommand,
    ConfirmPasswordResetUseCase,
)
from researchlens.modules.auth.application.disable_mfa import DisableMfaCommand, DisableMfaUseCase
from researchlens.modules.auth.application.dto import (
    AuthenticatedActor,
    AuthenticatedUserDto,
    AuthMfaChallengeResponseDto,
    AuthTokenResponseDto,
    AuthTokenResult,
    LogoutResponseDto,
    MfaEnabledResponseDto,
    MfaEnrollStartResponseDto,
    MfaStatusResponseDto,
    PasswordResetConfirmResponseDto,
    PasswordResetRequestResponseDto,
)
from researchlens.modules.auth.application.get_current_user import GetCurrentUserUseCase
from researchlens.modules.auth.application.get_mfa_status import GetMfaStatusUseCase
from researchlens.modules.auth.application.login_user import LoginUserCommand, LoginUserUseCase
from researchlens.modules.auth.application.logout_auth_session import LogoutAuthSessionUseCase
from researchlens.modules.auth.application.refresh_auth_session import RefreshAuthSessionUseCase
from researchlens.modules.auth.application.register_user import (
    RegisterUserCommand,
    RegisterUserUseCase,
)
from researchlens.modules.auth.application.request_password_reset import (
    RequestPasswordResetCommand,
    RequestPasswordResetUseCase,
)
from researchlens.modules.auth.application.start_mfa_enrollment import (
    StartMfaEnrollmentCommand,
    StartMfaEnrollmentUseCase,
)
from researchlens.modules.auth.application.verify_mfa_challenge import (
    VerifyMfaChallengeCommand,
    VerifyMfaChallengeUseCase,
)
from researchlens.modules.auth.application.verify_mfa_enrollment import (
    VerifyMfaEnrollmentCommand,
    VerifyMfaEnrollmentUseCase,
)

__all__ = [
    "AuthMfaChallengeResponseDto",
    "AuthTokenResponseDto",
    "AuthTokenResult",
    "AuthenticatedActor",
    "AuthenticatedUserDto",
    "ConfirmPasswordResetCommand",
    "ConfirmPasswordResetUseCase",
    "DisableMfaCommand",
    "DisableMfaUseCase",
    "GetCurrentUserUseCase",
    "GetMfaStatusUseCase",
    "LoginUserCommand",
    "LoginUserUseCase",
    "LogoutAuthSessionUseCase",
    "LogoutResponseDto",
    "MfaEnabledResponseDto",
    "MfaEnrollStartResponseDto",
    "MfaStatusResponseDto",
    "PasswordResetConfirmResponseDto",
    "PasswordResetRequestResponseDto",
    "RefreshAuthSessionUseCase",
    "RegisterUserCommand",
    "RegisterUserUseCase",
    "RequestPasswordResetCommand",
    "RequestPasswordResetUseCase",
    "StartMfaEnrollmentCommand",
    "StartMfaEnrollmentUseCase",
    "VerifyMfaChallengeCommand",
    "VerifyMfaChallengeUseCase",
    "VerifyMfaEnrollmentCommand",
    "VerifyMfaEnrollmentUseCase",
]
