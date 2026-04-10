from researchlens.modules.auth.application.dto import LogoutResponseDto
from researchlens.modules.auth.application.ports import (
    AuthRepository,
    Clock,
    TokenHasher,
    TransactionManager,
)


class LogoutAuthSessionUseCase:
    def __init__(
        self,
        *,
        repository: AuthRepository,
        transaction_manager: TransactionManager,
        refresh_token_hasher: TokenHasher,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager
        self._refresh_token_hasher = refresh_token_hasher
        self._clock = clock

    async def execute(self, *, refresh_token: str | None) -> LogoutResponseDto:
        if not refresh_token:
            return LogoutResponseDto()

        token_hash = self._refresh_token_hasher.hash_token(refresh_token)
        async with self._transaction_manager.boundary():
            token_record = await self._repository.get_refresh_token_by_hash(token_hash=token_hash)
            if token_record is None:
                return LogoutResponseDto()
            now = self._clock.now()
            await self._repository.save_refresh_token(
                refresh_token=token_record.revoke(revoked_at=now)
            )
            session = await self._repository.get_session(session_id=token_record.session_id)
            if session is not None:
                await self._repository.save_session(session=session.revoke(revoked_at=now))
        return LogoutResponseDto()
