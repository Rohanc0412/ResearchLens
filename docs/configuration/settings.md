# Settings

Phase 3 centralizes backend configuration under `researchlens.shared.config` using `pydantic-settings`.

## Principles

- Settings are grouped by subsystem instead of being read ad hoc from scattered `os.getenv` calls.
- `packages/backend/pyproject.toml` is the canonical backend dependency source.
- API, worker, tests, and Alembic all load the same typed settings surface.
- Validation fails fast for incompatible or unsafe configuration combinations.

## Subsystems

- `app`: environment, debug flag, phase identifier, API host and port, worker name
- `database`: URL, echo flag, pooling defaults, startup migration toggle
- `bootstrap_actor`: retained typed settings group for older bootstrap context, no longer the normal protected-route identity path
- `auth`: auth enablement flags, JWT issuer/secret, access-token lifetime, refresh-cookie behavior, refresh/reset token secrets, password reset lifetime, TOTP MFA settings, registration toggle, dev-mode secret safety
- `smtp`: enablement, host, port, credentials, sender identity
- `retrieval`: feature toggles and safety limits
- `llm`: provider selection and credentials
- `embeddings`: provider selection, model, credentials, cache behavior
- `observability`: service name, log level, JSON logs, tracing toggle
- `queue`: backend mode, URL, polling interval
- `storage`: local or S3 mode, local artifact root, bucket, endpoint

## Validation

Startup validation currently rejects at least these cases:

- production with insecure auth defaults
- production with in-memory queue backend
- production with local-only storage mode
- enabled LLM provider without credentials
- OpenAI embeddings without credentials
- redis queue mode without a queue URL
- S3 storage mode without a bucket
- SMTP enabled without a host
- production with SQLite as the database backend
- production with auth dev bypass enabled
- production with password reset token secret left at the dev default
- invalid refresh cookie SameSite value

## Usage

Use `researchlens.shared.config.get_settings()` as the single settings entrypoint. Tests should reset the cache between scenarios with `reset_settings_cache()`.

## Phase 3 auth note

The Phase 2 `bootstrap_actor` settings are no longer the normal identity path for protected routes. Protected project routes now resolve an authenticated actor from the bearer access token through the auth runtime.

Important auth settings include:

- `AUTH_ACCESS_TOKEN_SECRET`
- `AUTH_REFRESH_TOKEN_SECRET`
- `AUTH_PASSWORD_RESET_TOKEN_SECRET`
- `AUTH_JWT_ISSUER`
- `AUTH_ACCESS_TOKEN_TTL_MINUTES`
- `AUTH_REFRESH_TOKEN_TTL_DAYS`
- `AUTH_REFRESH_COOKIE_NAME`
- `AUTH_REFRESH_COOKIE_SECURE`
- `AUTH_REFRESH_COOKIE_SAMESITE`
- `AUTH_ALLOW_REGISTER`
- `AUTH_PASSWORD_RESET_MINUTES`
- `AUTH_MFA_CHALLENGE_MINUTES`
- `AUTH_MFA_TOTP_ISSUER`
- `AUTH_MFA_TOTP_PERIOD_SECONDS`
- `AUTH_MFA_TOTP_DIGITS`
- `AUTH_MFA_TOTP_WINDOW`

Tests set `AUTH_REFRESH_COOKIE_SECURE=false` for local TestClient cookie flows. Production must not use the dev token secrets or dev bypass.
