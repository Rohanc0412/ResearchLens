from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from researchlens.modules.auth.application import (
    AuthenticatedActor,
    AuthTokenResult,
    ConfirmPasswordResetCommand,
    ConfirmPasswordResetUseCase,
    DisableMfaCommand,
    DisableMfaUseCase,
    GetCurrentUserUseCase,
    GetMfaStatusUseCase,
    LoginUserCommand,
    LoginUserUseCase,
    LogoutAuthSessionUseCase,
    RefreshAuthSessionUseCase,
    RegisterUserCommand,
    RegisterUserUseCase,
    RequestPasswordResetCommand,
    RequestPasswordResetUseCase,
    StartMfaEnrollmentCommand,
    StartMfaEnrollmentUseCase,
    VerifyMfaChallengeCommand,
    VerifyMfaChallengeUseCase,
    VerifyMfaEnrollmentCommand,
    VerifyMfaEnrollmentUseCase,
)
from researchlens.modules.auth.presentation.dependencies import (
    BearerToken,
    get_authenticated_actor,
    get_confirm_password_reset_use_case,
    get_current_user_use_case,
    get_disable_mfa_use_case,
    get_login_user_use_case,
    get_logout_auth_session_use_case,
    get_mfa_status_use_case,
    get_refresh_auth_session_use_case,
    get_register_user_use_case,
    get_request_password_reset_use_case,
    get_start_mfa_enrollment_use_case,
    get_verify_mfa_challenge_use_case,
    get_verify_mfa_enrollment_use_case,
)
from researchlens.modules.auth.presentation.refresh_cookie import (
    clear_refresh_cookie,
    set_refresh_cookie,
)
from researchlens.modules.auth.presentation.request_models import (
    LoginRequestDto,
    MfaChallengeVerifyRequestDto,
    MfaDisableRequestDto,
    MfaEnrollVerifyRequestDto,
    PasswordResetConfirmRequestDto,
    PasswordResetRequestDto,
    RegisterRequestDto,
)
from researchlens.modules.auth.presentation.response_models import (
    AuthenticatedUserDto,
    AuthMfaChallengeResponseDto,
    AuthTokenResponseDto,
    LogoutResponseDto,
    MfaEnabledResponseDto,
    MfaEnrollStartResponseDto,
    MfaStatusResponseDto,
    PasswordResetConfirmResponseDto,
    PasswordResetRequestResponseDto,
)

router = APIRouter(prefix="/auth", tags=["auth"])

RegisterUseCaseDep = Annotated[RegisterUserUseCase, Depends(get_register_user_use_case)]
LoginUseCaseDep = Annotated[LoginUserUseCase, Depends(get_login_user_use_case)]
RefreshUseCaseDep = Annotated[
    RefreshAuthSessionUseCase,
    Depends(get_refresh_auth_session_use_case),
]
LogoutUseCaseDep = Annotated[LogoutAuthSessionUseCase, Depends(get_logout_auth_session_use_case)]
CurrentUserUseCaseDep = Annotated[GetCurrentUserUseCase, Depends(get_current_user_use_case)]
RequestPasswordResetUseCaseDep = Annotated[
    RequestPasswordResetUseCase,
    Depends(get_request_password_reset_use_case),
]
ConfirmPasswordResetUseCaseDep = Annotated[
    ConfirmPasswordResetUseCase,
    Depends(get_confirm_password_reset_use_case),
]
MfaStatusUseCaseDep = Annotated[GetMfaStatusUseCase, Depends(get_mfa_status_use_case)]
StartMfaEnrollmentUseCaseDep = Annotated[
    StartMfaEnrollmentUseCase,
    Depends(get_start_mfa_enrollment_use_case),
]
VerifyMfaEnrollmentUseCaseDep = Annotated[
    VerifyMfaEnrollmentUseCase,
    Depends(get_verify_mfa_enrollment_use_case),
]
VerifyMfaChallengeUseCaseDep = Annotated[
    VerifyMfaChallengeUseCase,
    Depends(get_verify_mfa_challenge_use_case),
]
DisableMfaUseCaseDep = Annotated[DisableMfaUseCase, Depends(get_disable_mfa_use_case)]


@router.post(
    "/register",
    response_model=AuthTokenResponseDto,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequestDto,
    request: Request,
    response: Response,
    use_case: RegisterUseCaseDep,
) -> AuthTokenResponseDto:
    result = await use_case.execute(
        RegisterUserCommand(
            username=payload.username,
            email=str(payload.email),
            password=payload.password,
        )
    )
    set_refresh_cookie(request=request, response=response, result=result)
    return result.response


@router.post(
    "/login",
    response_model=AuthTokenResponseDto | AuthMfaChallengeResponseDto,
)
async def login(
    payload: LoginRequestDto,
    request: Request,
    response: Response,
    use_case: LoginUseCaseDep,
) -> AuthTokenResponseDto | AuthMfaChallengeResponseDto:
    result = await use_case.execute(
        LoginUserCommand(identifier=payload.identifier, password=payload.password)
    )
    if isinstance(result, AuthTokenResult):
        set_refresh_cookie(request=request, response=response, result=result)
    return result.response


@router.post("/refresh", response_model=AuthTokenResponseDto)
async def refresh(
    request: Request,
    response: Response,
    use_case: RefreshUseCaseDep,
) -> AuthTokenResponseDto:
    cookie_name = request.app.state.bootstrap.settings.auth.refresh_cookie_name
    result = await use_case.execute(refresh_token=request.cookies.get(cookie_name, ""))
    set_refresh_cookie(request=request, response=response, result=result)
    return result.response


@router.post("/logout", response_model=LogoutResponseDto)
async def logout(
    request: Request,
    response: Response,
    use_case: LogoutUseCaseDep,
) -> LogoutResponseDto:
    cookie_name = request.app.state.bootstrap.settings.auth.refresh_cookie_name
    result = await use_case.execute(refresh_token=request.cookies.get(cookie_name))
    clear_refresh_cookie(request=request, response=response)
    return result


@router.get("/me", response_model=AuthenticatedUserDto)
async def me(
    token: BearerToken,
    use_case: CurrentUserUseCaseDep,
) -> AuthenticatedUserDto:
    return await use_case.execute(access_token=token)


@router.post("/password-reset/request", response_model=PasswordResetRequestResponseDto)
async def request_password_reset(
    payload: PasswordResetRequestDto,
    use_case: RequestPasswordResetUseCaseDep,
) -> PasswordResetRequestResponseDto:
    return await use_case.execute(RequestPasswordResetCommand(email=str(payload.email)))


@router.post("/password-reset/confirm", response_model=PasswordResetConfirmResponseDto)
async def confirm_password_reset(
    payload: PasswordResetConfirmRequestDto,
    use_case: ConfirmPasswordResetUseCaseDep,
) -> PasswordResetConfirmResponseDto:
    return await use_case.execute(
        ConfirmPasswordResetCommand(token=payload.token, password=payload.password)
    )


@router.get("/mfa/status", response_model=MfaStatusResponseDto)
async def mfa_status(
    actor: Annotated[AuthenticatedActor, Depends(get_authenticated_actor)],
    use_case: MfaStatusUseCaseDep,
) -> MfaStatusResponseDto:
    return await use_case.execute(user_id=actor.user_id)


@router.post("/mfa/enroll/start", response_model=MfaEnrollStartResponseDto)
async def start_mfa_enrollment(
    actor: Annotated[AuthenticatedActor, Depends(get_authenticated_actor)],
    use_case: StartMfaEnrollmentUseCaseDep,
) -> MfaEnrollStartResponseDto:
    return await use_case.execute(StartMfaEnrollmentCommand(user_id=actor.user_id))


@router.post("/mfa/enroll/verify", response_model=MfaEnabledResponseDto)
async def verify_mfa_enrollment(
    payload: MfaEnrollVerifyRequestDto,
    actor: Annotated[AuthenticatedActor, Depends(get_authenticated_actor)],
    use_case: VerifyMfaEnrollmentUseCaseDep,
) -> MfaEnabledResponseDto:
    return await use_case.execute(
        VerifyMfaEnrollmentCommand(user_id=actor.user_id, code=payload.code)
    )


@router.post("/mfa/verify", response_model=AuthTokenResponseDto)
async def verify_mfa_challenge(
    payload: MfaChallengeVerifyRequestDto,
    request: Request,
    response: Response,
    use_case: VerifyMfaChallengeUseCaseDep,
) -> AuthTokenResponseDto:
    result = await use_case.execute(
        VerifyMfaChallengeCommand(mfa_token=payload.mfa_token, code=payload.code)
    )
    set_refresh_cookie(request=request, response=response, result=result)
    return result.response


@router.post("/mfa/disable", response_model=MfaEnabledResponseDto)
async def disable_mfa(
    payload: MfaDisableRequestDto,
    actor: Annotated[AuthenticatedActor, Depends(get_authenticated_actor)],
    use_case: DisableMfaUseCaseDep,
) -> MfaEnabledResponseDto:
    return await use_case.execute(DisableMfaCommand(user_id=actor.user_id, code=payload.code))
