from uuid import UUID

from researchlens.modules.auth.application.dto import MfaStatusResponseDto
from researchlens.modules.auth.application.ports import AuthRepository


class GetMfaStatusUseCase:
    def __init__(self, *, repository: AuthRepository) -> None:
        self._repository = repository

    async def execute(self, *, user_id: UUID) -> MfaStatusResponseDto:
        factors = await self._repository.get_mfa_factors_for_user(user_id=user_id)
        return MfaStatusResponseDto(
            enabled=any(factor.enabled for factor in factors),
            pending=any(factor.pending for factor in factors),
        )
