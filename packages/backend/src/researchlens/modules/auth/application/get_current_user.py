from researchlens.modules.auth.application.dto import AuthenticatedActor, AuthenticatedUserDto
from researchlens.modules.auth.application.ports import AuthRepository, TokenIssuer
from researchlens.modules.auth.domain import User
from researchlens.shared.errors import AuthenticationError


class GetCurrentUserUseCase:
    def __init__(
        self,
        *,
        repository: AuthRepository,
        token_issuer: TokenIssuer,
    ) -> None:
        self._repository = repository
        self._token_issuer = token_issuer

    async def execute(self, *, access_token: str) -> AuthenticatedUserDto:
        user = await self.resolve_user(access_token=access_token)
        return AuthenticatedUserDto.from_user(user)

    async def execute_actor(self, *, access_token: str) -> AuthenticatedActor:
        user = await self.resolve_user(access_token=access_token)
        return AuthenticatedActor(
            user_id=user.id,
            tenant_id=user.tenant_id,
            roles=list(user.roles),
        )

    async def resolve_user(self, *, access_token: str) -> User:
        claims = self._token_issuer.verify_access_token(access_token)
        user = await self._repository.get_user_by_id(user_id=claims.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Invalid access token.")
        if user.tenant_id != claims.tenant_id:
            raise AuthenticationError("Invalid access token.")
        return user
