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

The web app uses this base URL for:

- generated API client requests
- refresh-cookie-aware auth restore
- authenticated artifact download requests
- authenticated run SSE streaming

## Session settings that directly affect the frontend

- `AUTH_REFRESH_COOKIE_NAME`
- `AUTH_REFRESH_COOKIE_SECURE`
- `AUTH_REFRESH_COOKIE_SAMESITE`
- `AUTH_ACCESS_TOKEN_TTL_MINUTES`
- `AUTH_REFRESH_TOKEN_TTL_DAYS`
- `QUEUE_SSE_KEEPALIVE_SECONDS`
- `QUEUE_SSE_TERMINAL_GRACE_SECONDS`

## Generated client workflow

Regenerate the TypeScript client after backend contract changes:

```bash
corepack pnpm --filter @researchlens/api-client run generate
```

That command exports FastAPI OpenAPI from the installed API package and regenerates `packages/api_client/src/generated`.
