# Phase 11 Completion

## Scope implemented

- frontend rebuild for auth, projects, conversations, runs, evidence, and artifacts
- generated TypeScript client from backend OpenAPI
- refresh-cookie-aware session restore and expiration handling
- MFA login challenge and security page flows
- canonical conversation-to-run UX with SSE progress
- artifact preview/download and evidence/source inspection views

## Frontend architecture summary

- `apps/web` now uses the target `app/pages/widgets/features/entities/shared` structure
- routing, providers, and shell live under `app/`
- generated-client TanStack Query hooks live near entity ownership
- widgets compose the product shell, run progress, artifact browser, and evidence overview

## Generated client summary

- added reproducible OpenAPI export script: `scripts/export_openapi.py`
- added package script: `corepack pnpm --filter @researchlens/api-client run generate`
- generated client output lives in `packages/api_client/src/generated`

## Auth and session hardening summary

- bootstrap restore via `/auth/refresh`
- protected request retry-once behavior for `401`
- logout clears session idempotently from the UI perspective
- MFA challenge, enrollment, verify, and disable flows are wired to backend routes

## Streaming UX summary

- run progress uses the canonical runs route
- JSON history and SSE are merged by `event_number`
- reconnect uses `Last-Event-ID`
- duplicate events are deduped client-side
- terminal closure stops reconnect loops

## Evidence and artifact UX summary

- run artifact list page with real downloads
- text-like artifact preview after download
- evidence summary and section trace panels
- snippet detail page with source metadata and external link-out when available
- evaluation summary and repair summary surfaced when exposed by current backend contracts

## Tests added or updated

- `apps/web/src/app/providers/AuthProvider.test.tsx`
- `apps/web/src/entities/run/run-stream.test.ts`
- `apps/web/src/pages/login/LoginPage.test.tsx`
- `apps/web/tests/phase11.e2e.spec.ts`

## Docs added or updated

- `README.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/module-boundaries.md`
- `docs/architecture/streaming-protocol.md`
- `docs/architecture/frontend-architecture.md`
- `docs/testing/test-strategy.md`
- `docs/configuration/settings.md`
- `docs/phase_reports/phase_11_completion.md`

## Open risks for Phase 12

- the backend still lacks a read endpoint for “latest run by conversation”, so the frontend remembers the last UI-created run ID locally for continuity
- artifact preview is intentionally limited to text-like outputs because the backend does not expose a richer preview contract
- the backend OpenAPI version string still reflects an earlier phase label and should be aligned with the actual release phase when backend release/versioning is revisited
