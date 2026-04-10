# Auth Module

Phase 3 implements auth as a dedicated backend module with strict public contracts and explicit session lifecycle state.

## Contracts

Public auth responses use centralized DTOs from the auth application/presentation contract surface:

- `AuthenticatedUserDto`: `user_id`, `username`, `email`, `tenant_id`, `roles`
- `AuthTokenResponseDto`: bearer access token, expiry, and `AuthenticatedUserDto`
- `AuthMfaChallengeResponseDto`: explicit MFA challenge response when an enabled factor exists
- status DTOs for logout and password reset responses
- `MfaStatusResponseDto` for the scaffolded MFA status endpoint

`/auth/me` returns `AuthenticatedUserDto` exactly. `user_id` is the UUID subject, `username` is the normalized username, and `tenant_id` is the tenant UUID. The access token uses `sub=user_id`; the username claim is only a convenience snapshot.

## Layering

- `domain`: user normalization, password policy, session/refresh/password reset invariants, MFA factor state
- `application`: use cases, strict DTOs, and ports for persistence, crypto, token issuing, mail, clock, and transactions
- `infrastructure`: SQLAlchemy rows/repository, bcrypt hashing, JWT, HMAC token hashing, random token generation, password reset mail capture, runtime assembly
- `presentation`: FastAPI request parsing, bearer/cookie handling, response shaping, and thin route delegation

Shared code remains generic. Auth-specific business policy does not live under `shared/`.

## Sessions And Tokens

Successful register/login creates an `auth_sessions` row and an `auth_refresh_tokens` row. Access tokens are short-lived JWTs with issuer, subject user id, tenant id, roles, issue/expiry times, and session id. Refresh tokens are opaque random values stored only as HMAC hashes.

Refresh rotates the current refresh token by revoking the used token and creating a new row linked to the same session. Logout revokes the current refresh token and session when present. Password reset confirmation marks the reset token used, updates the password hash, and revokes active sessions and refresh tokens for the user.

Password reset tokens are one-time opaque values stored only as HMAC hashes. Password reset request always returns `{"status": "ok"}` to avoid account enumeration.

## Password Policy

The centralized password policy enforces:

- length between 8 and 128 characters
- at least one uppercase letter, lowercase letter, digit, and special character
- no spaces
- not equal to or containing the username
- not equal to the email
- rejection of a small common weak password set

Registration and password reset confirmation both use the same policy before hashing.

## MFA Status

Phase 3 includes the MFA table and a truthful `GET /auth/mfa/status` endpoint. Full TOTP enrollment, challenge verification, and disable flows are intentionally deferred rather than exposing incomplete public endpoints.
