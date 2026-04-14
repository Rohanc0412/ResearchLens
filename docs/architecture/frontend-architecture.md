# Frontend Architecture

Phase 11 rebuilds the browser app around generated backend contracts and a hardened session model.

## Structure

`apps/web/src` is organized as:

- `app/`: providers, routes, layout, global theme
- `pages/`: route surfaces
- `widgets/`: composed product sections
- `features/`: user actions
- `entities/`: query keys, hooks, streaming logic, and domain-facing transport
- `shared/`: generic UI, env config, formatting, and transport helpers

## Generated client

- Source of truth: backend OpenAPI
- Package: `packages/api_client`
- Generation command: `corepack pnpm --filter @researchlens/api-client run generate`
- Thin handwritten code is limited to auth retry handling, SSE, and binary downloads

## Session flow

- Access tokens are held in memory.
- The refresh cookie is used on bootstrap through `/auth/refresh`.
- Protected requests retry once on `401`.
- If refresh fails, the app clears session state and redirects to `/login`.
- MFA challenge state is preserved in the auth provider until verification succeeds.

## Data fetching

- TanStack Query owns request caching and mutations.
- Query keys are small and module-scoped.
- Entity hooks call the generated client through the shared auth-aware request helper path.

## Streaming

- The run entity owns SSE parsing and reconnect behavior.
- JSON history and SSE events are merged by `event_number`.
- The UI stops reconnecting after terminal closure.

## UX surfaces

- `/login`: login, register, password reset request/confirm, MFA verification
- `/projects`: project list and project creation
- `/projects/:projectId`: project detail and conversation launch
- `/projects/:projectId/conversations/:conversationId`: full-bleed research workspace with header, persisted message timeline, docked composer, live run progress, and report/evidence surface
- `/runs/:runId/artifacts`: artifact list, preview, evidence linkage, evaluation/repair summary
- `/evidence/snippets/:snippetId`: chunk detail and source metadata
- `/security`: MFA status, enroll, verify, disable

## Design system

The app keeps the established Obsidian language:

- background `#0b0b0e`
- layered surfaces `#101015` and `#16161e`
- accent `#9580c4`
- Geist, Geist Mono, and Cal Sans
- compact row-oriented dashboard surfaces, thin borders, small radii, and mono metadata
- subtle Framer Motion transitions for page entry, sidebar width, dialogs, progress bars, and event reveals
