from datetime import timedelta
from uuid import UUID, uuid4

from researchlens.modules.auth.application.dto import (
    AuthenticatedUserDto,
    AuthTokenResponseDto,
    AuthTokenResult,
)
from researchlens.modules.auth.application.ports import (
    AuthRepository,
    Clock,
    OpaqueTokenGenerator,
    TokenHasher,
    TokenIssuer,
)
from researchlens.modules.auth.domain import RefreshToken, Session, User


class TokenLifecycle:
    def __init__(
        self,
        *,
        repository: AuthRepository,
        access_token_issuer: TokenIssuer,
        refresh_token_generator: OpaqueTokenGenerator,
        refresh_token_hasher: TokenHasher,
        clock: Clock,
        refresh_token_ttl_days: int,
    ) -> None:
        self._repository = repository
        self._access_token_issuer = access_token_issuer
        self._refresh_token_generator = refresh_token_generator
        self._refresh_token_hasher = refresh_token_hasher
        self._clock = clock
        self._refresh_token_ttl_days = refresh_token_ttl_days

    async def create_session_token(self, *, user: User) -> AuthTokenResult:
        now = self._clock.now()
        expires_at = now + timedelta(days=self._refresh_token_ttl_days)
        session = Session(
            id=uuid4(),
            user_id=user.id,
            tenant_id=user.tenant_id,
            created_at=now,
            expires_at=expires_at,
        )
        await self._repository.add_session(session=session)
        return await self.rotate_refresh_token(
            user=user,
            session=session,
            rotated_from_id=None,
        )

    async def rotate_refresh_token(
        self,
        *,
        user: User,
        session: Session,
        rotated_from_id: UUID | None,
    ) -> AuthTokenResult:
        now = self._clock.now()
        refresh_token = self._refresh_token_generator.generate()
        expires_at = now + timedelta(days=self._refresh_token_ttl_days)
        refresh_token_record = RefreshToken(
            id=uuid4(),
            session_id=session.id,
            user_id=user.id,
            tenant_id=user.tenant_id,
            token_hash=self._refresh_token_hasher.hash_token(refresh_token),
            created_at=now,
            expires_at=expires_at,
            rotated_from_id=rotated_from_id,
        )
        await self._repository.add_refresh_token(refresh_token=refresh_token_record)
        issued_access_token = self._access_token_issuer.issue_access_token(
            user=user,
            session_id=session.id,
            issued_at=now,
        )
        return AuthTokenResult(
            response=AuthTokenResponseDto(
                access_token=issued_access_token.token,
                expires_in=issued_access_token.expires_in,
                user=AuthenticatedUserDto.from_user(user),
            ),
            refresh_token=refresh_token,
            refresh_expires_at=expires_at,
        )
