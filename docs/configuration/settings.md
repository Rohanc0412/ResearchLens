# Settings

Backend configuration remains centralized under `researchlens.shared.config` with `pydantic-settings`.

For local and dev execution, Doppler is the runtime source of truth for both secrets and non-secret configuration. `.env.example` is reference-only and must mirror the supported env surface, but it is not the authority used to run the stack.

Recommended Doppler split:

- `dev` for host-mode local execution
- `compose-dev` for Docker Compose execution

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
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Required local browser settings:

```bash
APP_CORS_ALLOWED_ORIGINS=http://127.0.0.1:4173,http://localhost:4173
AUTH_REFRESH_COOKIE_SECURE=false
```

The web app uses this base URL for:

- generated API client requests
- refresh-cookie-aware auth restore
- authenticated artifact download requests
- authenticated run SSE streaming

## Session settings that directly affect the frontend

- `APP_CORS_ALLOWED_ORIGINS`
- `AUTH_REFRESH_COOKIE_NAME`
- `AUTH_REFRESH_COOKIE_SECURE`
- `AUTH_REFRESH_COOKIE_SAMESITE`
- `AUTH_ACCESS_TOKEN_TTL_MINUTES`
- `AUTH_REFRESH_TOKEN_TTL_DAYS`
- `QUEUE_SSE_KEEPALIVE_SECONDS`
- `QUEUE_SSE_TERMINAL_GRACE_SECONDS`

For local Doppler-backed development, set `AUTH_REFRESH_COOKIE_SECURE=false` in the active Doppler config. If Doppler injects `true`, browser session restore over `http://127.0.0.1` will still fail even though the code default is local-safe.

For compose-backed local development, set these values in the compose-specific Doppler config as well:

```bash
APP_API_HOST=0.0.0.0
DATABASE_URL=postgresql+psycopg://researchlens:researchlens@postgres:5432/researchlens
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Generated client workflow

Regenerate the TypeScript client after backend contract changes:

```bash
corepack pnpm --filter @researchlens/api-client run generate
```

That command exports FastAPI OpenAPI from the installed API package and regenerates `packages/api_client/src/generated`.
