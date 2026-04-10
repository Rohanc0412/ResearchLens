from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.auth.application.dto import MfaEnabledResponseDto
from researchlens.modules.auth.application.ports import (
    AuthRepository,
    Clock,
    TotpService,
    TransactionManager,
)
from researchlens.modules.auth.domain import TOTP_FACTOR_TYPE
from researchlens.shared.errors import ValidationError


@dataclass(frozen=True, slots=True)
class VerifyMfaEnrollmentCommand:
    user_id: UUID
    code: str


class VerifyMfaEnrollmentUseCase:
    def __init__(
        self,
        *,
        repository: AuthRepository,
        transaction_manager: TransactionManager,
        totp_service: TotpService,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager
        self._totp_service = totp_service
        self._clock = clock

    async def execute(self, command: VerifyMfaEnrollmentCommand) -> MfaEnabledResponseDto:
        async with self._transaction_manager.boundary():
            factor = await self._repository.get_mfa_factor(
                user_id=command.user_id,
                factor_type=TOTP_FACTOR_TYPE,
            )
            if factor is None or factor.enabled:
                raise ValidationError("Pending MFA enrollment was not found.")
            now = self._clock.now()
            if not self._totp_service.verify_code(
                secret=factor.secret,
                code=command.code,
                verified_at=now,
            ):
                raise ValidationError("Invalid MFA verification code.")

            await self._repository.save_mfa_factor(factor=factor.enable(enabled_at=now))
            return MfaEnabledResponseDto(enabled=True)
