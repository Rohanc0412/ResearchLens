# Settings

Backend configuration remains centralized under `researchlens.shared.config` with `pydantic-settings`.

For local and dev execution, Doppler is the runtime source of truth for both secrets and non-secret configuration. `.env.example` is reference-only and must mirror the supported env surface, but it is not the authority used to run the stack.

Recommended Doppler split:

- `dev` for host-mode local execution
- `dev_compose` for Docker Compose execution

That split keeps host-specific values such as `DATABASE_URL=...@localhost` separate from compose-safe values such as `DATABASE_URL=...@postgres` and `APP_API_HOST=0.0.0.0`.

## Backend settings groups

- `app`
- `database`
- `bootstrap_actor`
- `auth`
- `smtp`
- `retrieval`
- `drafting`
- `evaluation`
- `repair`
- `llm`
- `embeddings`
- `observability`
- `queue`
- `storage`

## Frontend settings

Phase 11 adds one frontend runtime setting:

- `VITE_API_BASE_URL`

Default local host-mode value:

```bash
VITE_API_BASE_URL=http://localhost:8017
```

Required local browser settings:

```bash
APP_CORS_ALLOWED_ORIGINS=http://localhost:4273
AUTH_REFRESH_COOKIE_SECURE=false
```

The web app uses this base URL for:

- generated API client requests
- refresh-cookie-aware auth restore
- authenticated artifact download requests
- authenticated run SSE streaming

## SMTP password reset delivery

When `SMTP_ENABLED=false`, password reset requests stay on the local capture mailer used by tests and local-only debugging.

When `SMTP_ENABLED=true`, the auth runtime sends password reset codes through the configured SMTP server using:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_STARTTLS`
- `SMTP_USERNAME` and `SMTP_PASSWORD` together when authenticated SMTP is required
- `SMTP_FROM_NAME`
- `SMTP_FROM_EMAIL`

## Session settings that directly affect the frontend

- `APP_CORS_ALLOWED_ORIGINS`
- `AUTH_REFRESH_COOKIE_NAME`
- `AUTH_REFRESH_COOKIE_SECURE`
- `AUTH_REFRESH_COOKIE_SAMESITE`
- `AUTH_ACCESS_TOKEN_TTL_MINUTES`
- `AUTH_REFRESH_TOKEN_TTL_DAYS`
- `QUEUE_SSE_KEEPALIVE_SECONDS`
- `QUEUE_SSE_TERMINAL_GRACE_SECONDS`

## Quick-answer web search

Conversation quick answers can optionally use web search during the `/conversations/{conversation_id}/send` SSE flow.

- `TAVILY_API_KEY` enables Tavily-backed web search for quick answers
- `CHAT_SEARCH_MODEL` optionally overrides the model used for quick-answer chat without changing the default `LLM_MODEL`

If `TAVILY_API_KEY` is unset, quick answers stay in pure LLM mode and no web-search status event is emitted.

## MFA TOTP behavior

- `AUTH_MFA_TOTP_PERIOD_SECONDS` defaults to `30`

ResearchLens accepts only the current TOTP step. A code from the previous or next 30-second window is rejected.

For local Doppler-backed development, set `AUTH_REFRESH_COOKIE_SECURE=false` in the active Doppler config. If Doppler injects `true`, browser session restore over `http://localhost` will still fail even though the code default is local-safe.

For compose-backed local development, set these values in the compose-specific Doppler config as well:

```bash
APP_API_HOST=0.0.0.0
DATABASE_URL=postgresql+psycopg://researchlens:researchlens@postgres:5432/researchlens
VITE_API_BASE_URL=http://localhost:8017
```

When `DATABASE_URL` targets the compose `postgres` service, the internal port must stay `5432`. The host-mapped `5547` port is only for processes running outside Docker.

## Generated client workflow

Regenerate the TypeScript client after backend contract changes:

```bash
corepack pnpm --filter @researchlens/api-client run generate
```

That command exports FastAPI OpenAPI from the installed API package and regenerates `packages/api_client/src/generated`.
