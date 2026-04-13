# Settings

Backend configuration remains centralized under `researchlens.shared.config` with `pydantic-settings`.

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

Default local value:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Local API/browser cross-origin settings:

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

For local Doppler-backed development, set `AUTH_REFRESH_COOKIE_SECURE=false` in the development config. If Doppler injects `true`, browser session restore over `http://127.0.0.1` will still fail even though the code default is local-safe.

## Generated client workflow

Regenerate the TypeScript client after backend contract changes:

```bash
corepack pnpm --filter @researchlens/api-client run generate
```

That command exports FastAPI OpenAPI from the installed API package and regenerates `packages/api_client/src/generated`.
