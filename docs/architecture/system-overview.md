# System Overview

ResearchLens is a modular-monolith backend plus a generated-client React frontend.

## Product shape

- `auth` owns register, login, refresh, logout, password reset, `/auth/me`, and MFA.
- `projects` owns project CRUD.
- `conversations` owns project-scoped conversations and persisted messages.
- `runs` owns lifecycle, queueing, checkpoints, SSE/JSON event streaming, cancel, and retry.
- `retrieval`, `drafting`, `evaluation`, `repair`, and `artifacts` remain backend-owned execution/read modules under the runs-owned LangGraph.
- `evidence` is read-focused and composes durable retrieval/drafting/evaluation/repair/artifact state without creating a second source of truth.

## Runtime split

- `apps/api` is composition-only HTTP transport.
- `apps/worker` is composition-only background execution.
- `apps/web` is the user-facing client.
- `packages/backend` is the canonical Python business package.
- `packages/api_client` is the generated TypeScript client package.

## Frontend architecture

The frontend follows the intended ownership model:

- `app/`: providers, routing, layouts, theme bootstrapping
- `pages/`: route-level surfaces only
- `widgets/`: composed product sections such as the sidebar, run progress card, artifact browser, and evidence overview
- `features/`: user actions such as creating projects and posting/researching messages
- `entities/`: query keys, generated-client transport hooks, and streaming/session integration near domain ownership
- `shared/`: generic UI, env config, formatting, and transport helpers

## Session and client model

- The browser uses a generated API client from backend OpenAPI.
- Access tokens stay in memory.
- Session restore happens on bootstrap through `/auth/refresh` with credentials enabled for the refresh cookie.
- Protected requests retry once on `401` by refreshing, then clear the session and redirect if refresh fails.
- MFA login challenge stays in the auth provider until the verification code completes the session.

## Run progress model

- Runs are started from the canonical `POST /conversations/{conversation_id}/runs` route.
- Historical events come from `GET /runs/{run_id}/events`.
- Live progress uses `Accept: text/event-stream` on the same route.
- The frontend reconnects with `Last-Event-ID`, dedupes by `event_number`, and stops reconnecting after terminal closure.

## Evidence and artifact model

- Evidence pages consume read-only evidence summary, section trace, chunk detail, and source detail contracts.
- Artifact pages list real persisted artifacts, preview text-like outputs by downloading backend bytes, and expose evaluation and repair summaries when present.

## Known limitation

The current backend does not expose a read route for “latest run by conversation”. The Phase 11 frontend therefore remembers the most recent run ID created from the UI for conversation continuity, while still treating run/evidence/artifact state as backend-owned.
