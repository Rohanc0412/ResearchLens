from dataclasses import dataclass

from researchlens.modules.auth.application.dto import (
    AuthenticatedUserDto,
    AuthMfaChallengeResponseDto,
    AuthTokenResult,
    MfaChallengeResult,
)
from researchlens.modules.auth.application.ports import (
    AuthRepository,
    Clock,
    PasswordHasher,
    TokenIssuer,
    TransactionManager,
)
from researchlens.modules.auth.application.token_lifecycle import TokenLifecycle
from researchlens.modules.auth.domain import normalize_email, normalize_username
from researchlens.shared.errors import AuthenticationError


@dataclass(frozen=True, slots=True)
class LoginUserCommand:
    identifier: str
    password: str


class LoginUserUseCase:
    def __init__(
        self,
        *,
        repository: AuthRepository,
        transaction_manager: TransactionManager,
        password_hasher: PasswordHasher,
        token_lifecycle: TokenLifecycle,
        token_issuer: TokenIssuer,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager
        self._password_hasher = password_hasher
        self._token_lifecycle = token_lifecycle
        self._token_issuer = token_issuer
        self._clock = clock

    async def execute(self, command: LoginUserCommand) -> AuthTokenResult | MfaChallengeResult:
        identifier = _normalize_identifier(command.identifier)
        credentials = await self._repository.get_user_credentials_by_identifier(
            identifier=identifier,
        )
        if credentials is None:
            raise AuthenticationError("Invalid credentials.")
        if not credentials.user.is_active:
            raise AuthenticationError("Invalid credentials.")
        if not self._password_hasher.verify_password(command.password, credentials.password_hash):
            raise AuthenticationError("Invalid credentials.")

        factors = await self._repository.get_mfa_factors_for_user(user_id=credentials.user.id)
        if any(factor.enabled for factor in factors):
            token = self._token_issuer.issue_mfa_challenge(
                user=credentials.user,
                issued_at=self._clock.now(),
            )
            return MfaChallengeResult(
                response=AuthMfaChallengeResponseDto(
                    mfa_token=token,
                    user=AuthenticatedUserDto.from_user(credentials.user),
                )
            )

        async with self._transaction_manager.boundary():
            return await self._token_lifecycle.create_session_token(user=credentials.user)


def _normalize_identifier(identifier: str) -> str:
    if "@" in identifier:
        return normalize_email(identifier)
    return normalize_username(identifier)
