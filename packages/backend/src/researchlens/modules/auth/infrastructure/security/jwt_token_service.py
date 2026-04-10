from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID

import jwt

from researchlens.modules.auth.application.ports import AccessTokenClaims, IssuedAccessToken
from researchlens.modules.auth.domain import User
from researchlens.shared.errors import AuthenticationError

_ALGORITHM = "HS256"


class JwtTokenService:
    def __init__(
        self,
        *,
        secret: str,
        issuer: str,
        access_token_minutes: int,
        clock_skew_seconds: int,
        mfa_challenge_minutes: int,
    ) -> None:
        self._secret = secret
        self._issuer = issuer
        self._access_token_minutes = access_token_minutes
        self._clock_skew_seconds = clock_skew_seconds
        self._mfa_challenge_minutes = mfa_challenge_minutes

    def issue_access_token(
        self,
        *,
        user: User,
        session_id: UUID,
        issued_at: datetime,
    ) -> IssuedAccessToken:
        expires_at = issued_at + timedelta(minutes=self._access_token_minutes)
        claims = {
            "typ": "access",
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "roles": list(user.roles),
            "iss": self._issuer,
            "iat": issued_at,
            "exp": expires_at,
            "session_id": str(session_id),
            "username": user.username,
        }
        token = jwt.encode(claims, self._secret, algorithm=_ALGORITHM)
        return IssuedAccessToken(
            token=token,
            expires_in=int((expires_at - issued_at).total_seconds()),
        )

    def verify_access_token(self, token: str) -> AccessTokenClaims:
        claims = self._decode(token, error_message="Invalid access token.")
        if claims.get("typ") != "access":
            raise AuthenticationError("Invalid access token.")

        return _claims_from_payload(claims, error_message="Invalid access token.")

    def issue_mfa_challenge(self, *, user: User, issued_at: datetime) -> str:
        expires_at = issued_at + timedelta(minutes=self._mfa_challenge_minutes)
        return jwt.encode(
            {
                "typ": "mfa",
                "sub": str(user.id),
                "tenant_id": str(user.tenant_id),
                "roles": list(user.roles),
                "iss": self._issuer,
                "iat": issued_at,
                "exp": expires_at,
            },
            self._secret,
            algorithm=_ALGORITHM,
        )

    def verify_mfa_challenge(self, token: str) -> AccessTokenClaims:
        claims = self._decode(token, error_message="Invalid MFA challenge token.")
        if claims.get("typ") != "mfa":
            raise AuthenticationError("Invalid MFA challenge token.")
        return _claims_from_payload(claims, error_message="Invalid MFA challenge token.")

    def _decode(self, token: str, *, error_message: str) -> dict[str, object]:
        try:
            return cast(
                dict[str, object],
                jwt.decode(
                    token,
                    self._secret,
                    algorithms=[_ALGORITHM],
                    issuer=self._issuer,
                    leeway=self._clock_skew_seconds,
                ),
            )
        except jwt.InvalidTokenError as exc:
            raise AuthenticationError(error_message) from exc


def utc_now() -> datetime:
    return datetime.now(UTC)


def _claims_from_payload(
    claims: dict[str, object],
    *,
    error_message: str,
) -> AccessTokenClaims:
    try:
        roles = claims["roles"]
        if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
            raise ValueError
        session_id = claims.get("session_id")
        return AccessTokenClaims(
            user_id=UUID(str(claims["sub"])),
            tenant_id=UUID(str(claims["tenant_id"])),
            roles=roles,
            session_id=UUID(str(session_id)) if session_id else None,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise AuthenticationError(error_message) from exc
