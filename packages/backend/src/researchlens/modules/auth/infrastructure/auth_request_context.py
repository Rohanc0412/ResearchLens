from dataclasses import dataclass

from researchlens.modules.auth.application import (
    ConfirmPasswordResetUseCase,
    DisableMfaUseCase,
    GetCurrentUserUseCase,
    GetMfaStatusUseCase,
    LoginUserUseCase,
    LogoutAuthSessionUseCase,
    RefreshAuthSessionUseCase,
    RegisterUserUseCase,
    RequestPasswordResetUseCase,
    StartMfaEnrollmentUseCase,
    VerifyMfaChallengeUseCase,
    VerifyMfaEnrollmentUseCase,
)


@dataclass(slots=True)
class AuthRequestContext:
    register_user: RegisterUserUseCase
    login_user: LoginUserUseCase
    refresh_auth_session: RefreshAuthSessionUseCase
    logout_auth_session: LogoutAuthSessionUseCase
    get_current_user: GetCurrentUserUseCase
    request_password_reset: RequestPasswordResetUseCase
    confirm_password_reset: ConfirmPasswordResetUseCase
    get_mfa_status: GetMfaStatusUseCase
    start_mfa_enrollment: StartMfaEnrollmentUseCase
    verify_mfa_enrollment: VerifyMfaEnrollmentUseCase
    verify_mfa_challenge: VerifyMfaChallengeUseCase
    disable_mfa: DisableMfaUseCase
