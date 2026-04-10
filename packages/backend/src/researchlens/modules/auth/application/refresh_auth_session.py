from researchlens.modules.auth.application.dto import AuthTokenResult
from researchlens.modules.auth.application.ports import (
    AuthRepository,
    Clock,
    TokenHasher,
    TransactionManager,
)
from researchlens.modules.auth.application.token_lifecycle import TokenLifecycle
from researchlens.shared.errors import AuthenticationError


class RefreshAuthSessionUseCase:
    def __init__(
        self,
        *,
        repository: AuthRepository,
        transaction_manager: TransactionManager,
        refresh_token_hasher: TokenHasher,
        token_lifecycle: TokenLifecycle,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager
        self._refresh_token_hasher = refresh_token_hasher
        self._token_lifecycle = token_lifecycle
        self._clock = clock

    async def execute(self, *, refresh_token: str) -> AuthTokenResult:
        token_hash = self._refresh_token_hasher.hash_token(refresh_token)
        async with self._transaction_manager.boundary():
            token_record = await self._repository.get_refresh_token_by_hash(token_hash=token_hash)
            if token_record is None:
                raise AuthenticationError("Invalid refresh token.")

            now = self._clock.now()
            token_record.require_usable(now=now)
            session = await self._repository.get_session(session_id=token_record.session_id)
            if session is None:
                raise AuthenticationError("Invalid refresh token.")
            session.require_usable(now=now)
            user = await self._repository.get_user_by_id(user_id=token_record.user_id)
            if user is None or not user.is_active:
                raise AuthenticationError("Invalid refresh token.")

            await self._repository.save_refresh_token(
                refresh_token=token_record.mark_used(used_at=now).revoke(revoked_at=now)
            )
            await self._repository.save_session(session=session.mark_used(used_at=now))
            return await self._token_lifecycle.rotate_refresh_token(
                user=user,
                session=session,
                rotated_from_id=token_record.id,
            )
