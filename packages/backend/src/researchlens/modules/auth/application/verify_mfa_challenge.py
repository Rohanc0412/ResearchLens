from dataclasses import dataclass

from researchlens.modules.auth.application.dto import AuthTokenResult
from researchlens.modules.auth.application.ports import (
    AuthRepository,
    Clock,
    TokenIssuer,
    TotpService,
    TransactionManager,
)
from researchlens.modules.auth.application.token_lifecycle import TokenLifecycle
from researchlens.modules.auth.domain import TOTP_FACTOR_TYPE
from researchlens.shared.errors import AuthenticationError


@dataclass(frozen=True, slots=True)
class VerifyMfaChallengeCommand:
    mfa_token: str
    code: str


class VerifyMfaChallengeUseCase:
    def __init__(
        self,
        *,
        repository: AuthRepository,
        transaction_manager: TransactionManager,
        token_issuer: TokenIssuer,
        totp_service: TotpService,
        token_lifecycle: TokenLifecycle,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager
        self._token_issuer = token_issuer
        self._totp_service = totp_service
        self._token_lifecycle = token_lifecycle
        self._clock = clock

    async def execute(self, command: VerifyMfaChallengeCommand) -> AuthTokenResult:
        claims = self._token_issuer.verify_mfa_challenge(command.mfa_token)
        async with self._transaction_manager.boundary():
            user = await self._repository.get_user_by_id(user_id=claims.user_id)
            if user is None or not user.is_active or user.tenant_id != claims.tenant_id:
                raise AuthenticationError("Invalid MFA challenge token.")

            factor = await self._repository.get_mfa_factor(
                user_id=user.id,
                factor_type=TOTP_FACTOR_TYPE,
            )
            if factor is None or not factor.enabled:
                raise AuthenticationError("MFA factor is not enabled.")

            now = self._clock.now()
            if not self._totp_service.verify_code(
                secret=factor.secret,
                code=command.code,
                verified_at=now,
            ):
                raise AuthenticationError("Invalid MFA verification code.")

            await self._repository.save_mfa_factor(factor=factor.mark_used(used_at=now))
            return await self._token_lifecycle.create_session_token(user=user)
