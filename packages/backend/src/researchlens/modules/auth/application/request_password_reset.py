from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

from researchlens.modules.auth.application.dto import PasswordResetRequestResponseDto
from researchlens.modules.auth.application.ports import (
    AuthRepository,
    Clock,
    OpaqueTokenGenerator,
    PasswordResetMailer,
    TokenHasher,
    TransactionManager,
)
from researchlens.modules.auth.domain import PasswordResetToken, normalize_email


@dataclass(frozen=True, slots=True)
class RequestPasswordResetCommand:
    email: str


class RequestPasswordResetUseCase:
    def __init__(
        self,
        *,
        repository: AuthRepository,
        transaction_manager: TransactionManager,
        reset_token_generator: OpaqueTokenGenerator,
        reset_token_hasher: TokenHasher,
        mailer: PasswordResetMailer,
        clock: Clock,
        password_reset_minutes: int,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager
        self._reset_token_generator = reset_token_generator
        self._reset_token_hasher = reset_token_hasher
        self._mailer = mailer
        self._clock = clock
        self._password_reset_minutes = password_reset_minutes

    async def execute(
        self,
        command: RequestPasswordResetCommand,
    ) -> PasswordResetRequestResponseDto:
        email = normalize_email(command.email)
        user = await self._repository.get_user_by_email(email=email)
        if user is None or not user.is_active:
            return PasswordResetRequestResponseDto()

        raw_token = self._reset_token_generator.generate()
        now = self._clock.now()
        password_reset_token = PasswordResetToken(
            id=uuid4(),
            user_id=user.id,
            tenant_id=user.tenant_id,
            token_hash=self._reset_token_hasher.hash_token(raw_token),
            created_at=now,
            expires_at=now + timedelta(minutes=self._password_reset_minutes),
        )
        async with self._transaction_manager.boundary():
            await self._repository.add_password_reset_token(
                password_reset_token=password_reset_token,
            )
            await self._mailer.send_password_reset(email=user.email, token=raw_token)
        return PasswordResetRequestResponseDto()
