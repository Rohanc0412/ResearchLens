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
class DisableMfaCommand:
    user_id: UUID
    code: str


class DisableMfaUseCase:
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

    async def execute(self, command: DisableMfaCommand) -> MfaEnabledResponseDto:
        async with self._transaction_manager.boundary():
            factor = await self._repository.get_mfa_factor(
                user_id=command.user_id,
                factor_type=TOTP_FACTOR_TYPE,
            )
            if factor is None or not factor.enabled:
                raise ValidationError("MFA is not enabled.")
            if not self._totp_service.verify_code(
                secret=factor.secret,
                code=command.code,
                verified_at=self._clock.now(),
            ):
                raise ValidationError("Invalid MFA verification code.")

            await self._repository.delete_mfa_factor(factor_id=factor.id)
            return MfaEnabledResponseDto(enabled=False)
