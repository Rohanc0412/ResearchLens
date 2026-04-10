from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from typing import Annotated, Protocol, cast

from fastapi import Depends, Request

from researchlens.modules.auth.application import (
    AuthenticatedActor,
    ConfirmPasswordResetUseCase,
    GetCurrentUserUseCase,
    GetMfaStatusUseCase,
    LoginUserUseCase,
    LogoutAuthSessionUseCase,
    RefreshAuthSessionUseCase,
    RegisterUserUseCase,
    RequestPasswordResetUseCase,
)
from researchlens.shared.errors import AuthenticationError


class AuthRequestContext(Protocol):
    register_user: RegisterUserUseCase
    login_user: LoginUserUseCase
    refresh_auth_session: RefreshAuthSessionUseCase
    logout_auth_session: LogoutAuthSessionUseCase
    get_current_user: GetCurrentUserUseCase
    request_password_reset: RequestPasswordResetUseCase
    confirm_password_reset: ConfirmPasswordResetUseCase
    get_mfa_status: GetMfaStatusUseCase


class AuthRuntime(Protocol):
    def request_context(self) -> AbstractAsyncContextManager[AuthRequestContext]: ...


async def get_auth_context(request: Request) -> AsyncIterator[AuthRequestContext]:
    runtime = cast(AuthRuntime, request.app.state.bootstrap.auth_runtime)
    async with runtime.request_context() as context:
        yield context


def get_bearer_access_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise AuthenticationError("Bearer access token is required.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError("Bearer access token is required.")
    return token


AuthContext = Annotated[AuthRequestContext, Depends(get_auth_context)]
BearerToken = Annotated[str, Depends(get_bearer_access_token)]


def get_register_user_use_case(context: AuthContext) -> RegisterUserUseCase:
    return context.register_user


def get_login_user_use_case(context: AuthContext) -> LoginUserUseCase:
    return context.login_user


def get_refresh_auth_session_use_case(context: AuthContext) -> RefreshAuthSessionUseCase:
    return context.refresh_auth_session


def get_logout_auth_session_use_case(context: AuthContext) -> LogoutAuthSessionUseCase:
    return context.logout_auth_session


def get_current_user_use_case(context: AuthContext) -> GetCurrentUserUseCase:
    return context.get_current_user


def get_request_password_reset_use_case(context: AuthContext) -> RequestPasswordResetUseCase:
    return context.request_password_reset


def get_confirm_password_reset_use_case(context: AuthContext) -> ConfirmPasswordResetUseCase:
    return context.confirm_password_reset


def get_mfa_status_use_case(context: AuthContext) -> GetMfaStatusUseCase:
    return context.get_mfa_status


async def get_authenticated_actor(
    token: BearerToken,
    use_case: Annotated[GetCurrentUserUseCase, Depends(get_current_user_use_case)],
) -> AuthenticatedActor:
    return await use_case.execute_actor(access_token=token)
