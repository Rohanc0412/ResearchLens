from dataclasses import dataclass

from researchlens.modules.auth.application.dto import PasswordResetConfirmResponseDto
from researchlens.modules.auth.application.ports import (
    AuthRepository,
    Clock,
    PasswordHasher,
    TokenHasher,
    TransactionManager,
)
from researchlens.modules.auth.domain import PasswordPolicy
from researchlens.shared.errors import ValidationError


@dataclass(frozen=True, slots=True)
class ConfirmPasswordResetCommand:
    token: str
    password: str


class ConfirmPasswordResetUseCase:
    def __init__(
        self,
        *,
        repository: AuthRepository,
        transaction_manager: TransactionManager,
        reset_token_hasher: TokenHasher,
        password_policy: PasswordPolicy,
        password_hasher: PasswordHasher,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager
        self._reset_token_hasher = reset_token_hasher
        self._password_policy = password_policy
        self._password_hasher = password_hasher
        self._clock = clock

    async def execute(
        self,
        command: ConfirmPasswordResetCommand,
    ) -> PasswordResetConfirmResponseDto:
        token_hash = self._reset_token_hasher.hash_token(command.token)
        async with self._transaction_manager.boundary():
            reset_token = await self._repository.get_password_reset_token_by_hash(
                token_hash=token_hash,
            )
            if reset_token is None:
                raise ValidationError("Password reset token is invalid.")

            now = self._clock.now()
            reset_token.require_usable(now=now)
            user = await self._repository.get_user_by_id(user_id=reset_token.user_id)
            if user is None or not user.is_active:
                raise ValidationError("Password reset token is invalid.")

            self._password_policy.validate(
                password=command.password,
                username=user.username,
                email=user.email,
            )
            password_hash = self._password_hasher.hash_password(command.password)
            await self._repository.update_user_password_hash(
                user_id=user.id,
                password_hash=password_hash,
                updated_at=now,
            )
            await self._repository.save_password_reset_token(
                password_reset_token=reset_token.mark_used(used_at=now),
            )
            await self._repository.revoke_active_refresh_tokens_for_user(
                user_id=user.id,
                revoked_at=now,
            )
            await self._repository.revoke_active_sessions_for_user(
                user_id=user.id,
                revoked_at=now,
            )
        return PasswordResetConfirmResponseDto()
