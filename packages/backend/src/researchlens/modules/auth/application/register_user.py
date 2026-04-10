from dataclasses import dataclass
from uuid import uuid4

from researchlens.modules.auth.application.dto import AuthTokenResult
from researchlens.modules.auth.application.ports import (
    AuthRepository,
    Clock,
    PasswordHasher,
    TransactionManager,
)
from researchlens.modules.auth.application.token_lifecycle import TokenLifecycle
from researchlens.modules.auth.domain import (
    PasswordPolicy,
    User,
    normalize_email,
    normalize_username,
)
from researchlens.shared.errors import ConflictError, ForbiddenError


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    username: str
    email: str
    password: str


class RegisterUserUseCase:
    def __init__(
        self,
        *,
        repository: AuthRepository,
        transaction_manager: TransactionManager,
        password_policy: PasswordPolicy,
        password_hasher: PasswordHasher,
        token_lifecycle: TokenLifecycle,
        clock: Clock,
        allow_register: bool,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager
        self._password_policy = password_policy
        self._password_hasher = password_hasher
        self._token_lifecycle = token_lifecycle
        self._clock = clock
        self._allow_register = allow_register

    async def execute(self, command: RegisterUserCommand) -> AuthTokenResult:
        if not self._allow_register:
            raise ForbiddenError("Registration is disabled.")

        username = normalize_username(command.username)
        email = normalize_email(command.email)
        self._password_policy.validate(
            password=command.password,
            username=username,
            email=email,
        )

        async with self._transaction_manager.boundary():
            if await self._repository.get_user_by_username(username=username):
                raise ConflictError("Username is already registered.")
            if await self._repository.get_user_by_email(email=email):
                raise ConflictError("Email is already registered.")

            now = self._clock.now()
            user = User.create(
                id=uuid4(),
                tenant_id=uuid4(),
                username=username,
                email=email,
                roles=["owner"],
                created_at=now,
                updated_at=now,
            )
            password_hash = self._password_hasher.hash_password(command.password)
            await self._repository.add_user(user=user, password_hash=password_hash)
            return await self._token_lifecycle.create_session_token(user=user)
