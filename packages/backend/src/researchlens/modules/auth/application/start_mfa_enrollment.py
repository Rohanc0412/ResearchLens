from dataclasses import dataclass
from uuid import UUID, uuid4

from researchlens.modules.auth.application.dto import MfaEnrollStartResponseDto
from researchlens.modules.auth.application.ports import (
    AuthRepository,
    Clock,
    TotpService,
    TransactionManager,
)
from researchlens.modules.auth.domain import TOTP_FACTOR_TYPE, MfaFactor
from researchlens.shared.errors import AuthenticationError, ConflictError


@dataclass(frozen=True, slots=True)
class StartMfaEnrollmentCommand:
    user_id: UUID


class StartMfaEnrollmentUseCase:
    def __init__(
        self,
        *,
        repository: AuthRepository,
        transaction_manager: TransactionManager,
        totp_service: TotpService,
        clock: Clock,
        issuer: str,
        period_seconds: int,
        digits: int,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager
        self._totp_service = totp_service
        self._clock = clock
        self._issuer = issuer
        self._period_seconds = period_seconds
        self._digits = digits

    async def execute(self, command: StartMfaEnrollmentCommand) -> MfaEnrollStartResponseDto:
        async with self._transaction_manager.boundary():
            user = await self._repository.get_user_by_id(user_id=command.user_id)
            if user is None or not user.is_active:
                raise AuthenticationError("Invalid access token.")
            existing = await self._repository.get_mfa_factor(
                user_id=user.id,
                factor_type=TOTP_FACTOR_TYPE,
            )
            if existing and existing.enabled:
                raise ConflictError("MFA is already enabled.")

            secret = self._totp_service.generate_secret()
            now = self._clock.now()
            if existing is None:
                factor = MfaFactor.create_totp(
                    id=uuid4(),
                    user_id=user.id,
                    tenant_id=user.tenant_id,
                    secret=secret,
                    created_at=now,
                )
                await self._repository.add_mfa_factor(factor=factor)
            else:
                factor = existing.replace_pending_secret(secret=secret, created_at=now)
                await self._repository.save_mfa_factor(factor=factor)

            return MfaEnrollStartResponseDto(
                secret=secret,
                otpauth_uri=self._totp_service.provisioning_uri(
                    secret=secret,
                    account_name=user.email,
                ),
                issuer=self._issuer,
                account_name=user.email,
                period=self._period_seconds,
                digits=self._digits,
            )
