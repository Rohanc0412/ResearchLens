# Auth Module

Phase 3 implements auth as a dedicated backend module with strict public contracts and explicit session lifecycle state.

## Contracts

Public auth responses use centralized DTOs from the auth application/presentation contract surface:

- `AuthenticatedUserDto`: `user_id`, `username`, `email`, `tenant_id`, `roles`
- `AuthTokenResponseDto`: bearer access token, expiry, and `AuthenticatedUserDto`
- `AuthMfaChallengeResponseDto`: explicit MFA challenge response when an enabled factor exists
- status DTOs for logout and password reset responses
- `MfaStatusResponseDto`, `MfaEnrollStartResponseDto`, and simple enabled status DTOs for the TOTP MFA flow

`/auth/me` returns `AuthenticatedUserDto` exactly. `user_id` is the UUID subject, `username` is the normalized username, and `tenant_id` is the tenant UUID. The access token uses `sub=user_id`; the username claim is only a convenience snapshot.

## Layering

- `domain`: user normalization, password policy, session/refresh/password reset invariants, MFA factor state
- `application`: use cases, strict DTOs, and ports for persistence, crypto, token issuing, TOTP, mail, clock, and transactions
- `infrastructure`: SQLAlchemy rows/repository, bcrypt hashing, JWT, HMAC token hashing, random token generation, TOTP, password reset mail capture/SMTP delivery, runtime assembly
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

## MFA

Phase 3 includes a complete TOTP MFA flow:

- `GET /auth/mfa/status` reports enabled and pending state.
- `POST /auth/mfa/enroll/start` creates or replaces a pending TOTP factor and returns the secret plus provisioning URI.
- `POST /auth/mfa/enroll/verify` verifies the current TOTP code and enables the factor.
- Login returns `AuthMfaChallengeResponseDto` instead of tokens when an enabled TOTP factor exists.
- `POST /auth/mfa/verify` verifies the short-lived MFA challenge token plus TOTP code, then creates the auth session and refresh cookie.
- `POST /auth/mfa/disable` verifies a current TOTP code and removes the factor.

TOTP generation and verification live in `auth.infrastructure.security`; route files do not implement TOTP or token logic.
