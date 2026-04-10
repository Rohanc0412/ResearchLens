# Phase 3 Completion Report

## Phase title

Auth module with strict contracts

## Scope restatement

Phase 3 implemented backend auth only: register, login, refresh, logout, `/auth/me`, password reset request/confirm, strict auth DTOs, centralized password policy enforcement, auth schema/lifecycle tests, and replacement of the Phase 2 protected-route `bootstrap_actor` identity path. Frontend auth flows, conversations, runs, retrieval, drafting, evaluation, repair, advanced org/tenant logic, and broad RBAC expansion stayed out of scope.

## Auth contract summary

- `AuthenticatedUserDto` is centralized and reused for `/auth/me` and token responses.
- `AuthTokenResponseDto` is reused for register, login success, and refresh success.
- Login can return `AuthMfaChallengeResponseDto` if an enabled MFA factor exists.
- Logout and password reset endpoints return strict status DTOs.
- Public request DTOs use `extra="forbid"` and public response DTOs do not use permissive extras.
- `/auth/me` resolves by access-token `sub=user_id` and persisted user/tenant state; `username` is returned from the user record, not from `user_id`.

## Session behavior summary

- Register/login create `auth_sessions` plus hashed `auth_refresh_tokens`.
- JWT access tokens include issuer, subject user id, tenant id, roles, issued/expiry times, session id, and username snapshot.
- Refresh tokens are opaque random values stored only as HMAC hashes.
- Refresh rotates tokens and revokes the used token.
- Logout revokes the current refresh token and session when present, and clears the cookie.
- Password reset confirmation revokes active sessions and refresh tokens for the user.

## Password policy summary

The centralized auth password policy enforces length, uppercase/lowercase/digit/special character requirements, no spaces, username/email exclusions, username substring rejection, and a small common weak password set. Registration and password reset confirmation both use this policy before hashing.

## Bootstrap actor replacement

Protected project routes no longer read `bootstrap_actor` settings as the normal identity path. They resolve a bearer-token-backed actor through the API composition auth runtime protocol and bind that tenant id for request logging. `/healthz` and `/health` remain public.

## Final endpoint list

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/password-reset/request`
- `POST /auth/password-reset/confirm`
- `GET /auth/mfa/status`

## MFA status

MFA is scaffolded, not fully implemented. The schema and status endpoint exist. TOTP enrollment, challenge verification, and disable flows are deferred to avoid weakening the core auth contract and session lifecycle work.

## Migrations added

- `20260409_0002_phase_3_auth.py`
- Tables: `auth_users`, `auth_sessions`, `auth_refresh_tokens`, `auth_password_resets`, `auth_mfa_factors`

## Tests added or updated

- Unit tests for username/email normalization, password policy validation, auth DTO strictness, bcrypt password hashing, HMAC token hashing, JWT issue/verify behavior, and auth domain invariants.
- Integration tests for register, duplicate username/email, weak password rejection, login by username/email, invalid credentials, refresh rotation, revoked/expired refresh behavior, logout revocation, `/auth/me` contract correctness, password reset request/confirm, invalid/expired/used reset tokens, weak reset password rejection, reset-driven session revocation, MFA status, project route auth replacement, health, and migrations.
- Existing project API tests now register a real user and send bearer auth.

## Docs added or updated

- `README.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/module-boundaries.md`
- `docs/architecture/auth-module.md`
- `docs/configuration/settings.md`
- `docs/phase_reports/phase_3_completion.md`

## Open questions for frontend auth flows

- Exact client handling for refresh-cookie rotation and logout retry behavior.
- Whether registration should remain public and single-user-per-new-tenant with default `owner` role.
- UI timing and copy for password reset email delivery once a real SMTP adapter replaces the capture mailer.
- Full TOTP enrollment and challenge UX for a later MFA phase.

## Post-completion stabilization

- Replaced root Turbo script orchestration with recursive Corepack pnpm workspace scripts so `corepack pnpm test`, `typecheck`, `lint`, and `build` work in the local shell without a bare `pnpm` shim.
- Removed the unused Turbo dependency and root Turbo config.
- Made JS package clean scripts use Node filesystem removal instead of shell-specific PowerShell removal.
- Updated Makefile, justfile, and README command examples to use `python -m uv` and `corepack pnpm` in this shell.
- Applied Ruff's mechanical formatting to previously drifted backend placeholder/shared files.
- Lengthened the development JWT access-token secret default and unit-test secrets to avoid PyJWT HMAC key-length warnings in test runs.
