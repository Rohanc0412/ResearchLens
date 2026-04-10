from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchlens.modules.auth.application import (
    ConfirmPasswordResetUseCase,
    GetCurrentUserUseCase,
    GetMfaStatusUseCase,
    LoginUserUseCase,
    LogoutAuthSessionUseCase,
    RefreshAuthSessionUseCase,
    RegisterUserUseCase,
    RequestPasswordResetUseCase,
)
from researchlens.modules.auth.application.dto import AuthenticatedActor
from researchlens.modules.auth.application.token_lifecycle import TokenLifecycle
from researchlens.modules.auth.domain import PasswordPolicy
from researchlens.modules.auth.infrastructure.clock import SystemClock
from researchlens.modules.auth.infrastructure.email import CapturingPasswordResetMailer
from researchlens.modules.auth.infrastructure.repositories import SqlAlchemyAuthRepository
from researchlens.modules.auth.infrastructure.security import (
    BcryptPasswordHasher,
    HmacTokenHasher,
    JwtTokenService,
    OpaqueTokenGenerator,
)
from researchlens.shared.config import ResearchLensSettings
from researchlens.shared.db import SqlAlchemyTransactionManager


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


class SqlAlchemyAuthRuntime:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        settings: ResearchLensSettings,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings
        self.password_reset_mailer = CapturingPasswordResetMailer()
        self._clock = SystemClock()
        self._password_policy = PasswordPolicy()
        self._password_hasher = BcryptPasswordHasher()
        self._refresh_token_generator = OpaqueTokenGenerator()
        self._reset_token_generator = OpaqueTokenGenerator()
        self._refresh_token_hasher = HmacTokenHasher(secret=settings.auth.refresh_token_secret)
        self._reset_token_hasher = HmacTokenHasher(secret=settings.auth.password_reset_token_secret)
        self._token_issuer = JwtTokenService(
            secret=settings.auth.access_token_secret,
            issuer=settings.auth.jwt_issuer,
            access_token_minutes=settings.auth.access_token_ttl_minutes,
            clock_skew_seconds=settings.auth.clock_skew_seconds,
            mfa_challenge_minutes=settings.auth.mfa_challenge_minutes,
        )

    @asynccontextmanager
    async def request_context(self) -> AsyncIterator[AuthRequestContext]:
        async with self._session_factory() as session:
            yield self._build_context(session)

    async def resolve_actor(self, *, access_token: str) -> AuthenticatedActor:
        async with self.request_context() as context:
            return await context.get_current_user.execute_actor(access_token=access_token)

    def _build_context(self, session: AsyncSession) -> AuthRequestContext:
        repository = SqlAlchemyAuthRepository(session)
        transaction_manager = SqlAlchemyTransactionManager(session)
        token_lifecycle = self._build_token_lifecycle(repository)
        return AuthRequestContext(
            register_user=self._build_register_user_use_case(
                repository,
                transaction_manager,
                token_lifecycle,
            ),
            login_user=LoginUserUseCase(
                repository=repository,
                transaction_manager=transaction_manager,
                password_hasher=self._password_hasher,
                token_lifecycle=token_lifecycle,
                token_issuer=self._token_issuer,
                clock=self._clock,
            ),
            refresh_auth_session=RefreshAuthSessionUseCase(
                repository=repository,
                transaction_manager=transaction_manager,
                refresh_token_hasher=self._refresh_token_hasher,
                token_lifecycle=token_lifecycle,
                clock=self._clock,
            ),
            logout_auth_session=LogoutAuthSessionUseCase(
                repository=repository,
                transaction_manager=transaction_manager,
                refresh_token_hasher=self._refresh_token_hasher,
                clock=self._clock,
            ),
            get_current_user=self._build_get_current_user_use_case(repository),
            request_password_reset=self._build_request_password_reset_use_case(
                repository,
                transaction_manager,
            ),
            confirm_password_reset=self._build_confirm_password_reset_use_case(
                repository,
                transaction_manager,
            ),
            get_mfa_status=GetMfaStatusUseCase(repository=repository),
        )

    def _build_token_lifecycle(
        self,
        repository: SqlAlchemyAuthRepository,
    ) -> TokenLifecycle:
        token_lifecycle = TokenLifecycle(
            repository=repository,
            access_token_issuer=self._token_issuer,
            refresh_token_generator=self._refresh_token_generator,
            refresh_token_hasher=self._refresh_token_hasher,
            clock=self._clock,
            refresh_token_ttl_days=self._settings.auth.refresh_token_ttl_days,
        )
        return token_lifecycle

    def _build_register_user_use_case(
        self,
        repository: SqlAlchemyAuthRepository,
        transaction_manager: SqlAlchemyTransactionManager,
        token_lifecycle: TokenLifecycle,
    ) -> RegisterUserUseCase:
        return RegisterUserUseCase(
            repository=repository,
            transaction_manager=transaction_manager,
            password_policy=self._password_policy,
            password_hasher=self._password_hasher,
            token_lifecycle=token_lifecycle,
            clock=self._clock,
            allow_register=self._settings.auth.allow_register,
        )

    def _build_get_current_user_use_case(
        self,
        repository: SqlAlchemyAuthRepository,
    ) -> GetCurrentUserUseCase:
        return GetCurrentUserUseCase(
            repository=repository,
            token_issuer=self._token_issuer,
        )

    def _build_request_password_reset_use_case(
        self,
        repository: SqlAlchemyAuthRepository,
        transaction_manager: SqlAlchemyTransactionManager,
    ) -> RequestPasswordResetUseCase:
        return RequestPasswordResetUseCase(
            repository=repository,
            transaction_manager=transaction_manager,
            reset_token_generator=self._reset_token_generator,
            reset_token_hasher=self._reset_token_hasher,
            mailer=self.password_reset_mailer,
            clock=self._clock,
            password_reset_minutes=self._settings.auth.password_reset_minutes,
        )

    def _build_confirm_password_reset_use_case(
        self,
        repository: SqlAlchemyAuthRepository,
        transaction_manager: SqlAlchemyTransactionManager,
    ) -> ConfirmPasswordResetUseCase:
        return ConfirmPasswordResetUseCase(
            repository=repository,
            transaction_manager=transaction_manager,
            reset_token_hasher=self._reset_token_hasher,
            password_policy=self._password_policy,
            password_hasher=self._password_hasher,
            clock=self._clock,
        )
