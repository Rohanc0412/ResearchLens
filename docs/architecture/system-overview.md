# System Overview

ResearchLens is a phased monorepo rebuild. Phase 4 extends the Phase 3 foundation with project detail/update flows and a dedicated `conversations` slice for conversation, message, and run-trigger intent persistence.

## Monorepo structure

The repository is split into `apps/` and `packages/` so deployment-facing entrypoints stay separate from reusable code:

- `apps/api` is the HTTP/API surface. It remains thin and owns only composition: logging bootstrap, exception handlers, middleware, health routes, auth/projects router wiring, and request-scoped runtime assembly.
- `apps/worker` is the future background execution process. In Phase 2 it still remains thin and proves shared runtime bootstrap without adding queue behavior.
- `apps/web` is the future browser client. In Phase 0 it provides only a placeholder shell and disciplined folder structure.

- `packages/backend` is the canonical installable Python package for backend modules, typed config, shared DB runtime, migrations, and backend tests.
- `packages/api_client` is reserved for generated TypeScript client artifacts.
- `packages/ui` is reserved for generic frontend UI components shared across apps.

## Why split apps and packages

This separation keeps runtime entrypoints thin and dependency direction explicit:

- apps depend on packages
- packages do not depend on app-local folders
- reusable code remains installable and testable
- Docker, CI, pytest, and Alembic use the same installed-package boundaries as local development

## Phase 4 status

The backend currently includes:

- shared logging with request ID and tenant context
- async DB engine, session, and transaction primitives
- lazy runtime health checks for DB connectivity and schema readiness
- one migration-backed `projects` module with create, list, get, update, and delete
- one migration-backed `auth` module with register, login, refresh, logout, `/auth/me`, password reset request/confirm, and TOTP MFA enrollment/challenge/disable
- one migration-backed `conversations` module with project-scoped conversation CRUD, message persistence and reads, cursor-based conversation listing, and a minimal run-trigger recording shell
- worker bootstrap that reuses the same shared foundation

Phase 3 replaced the Phase 2 `bootstrap_actor` protected-route identity path with auth-backed bearer token resolution. Phase 4 keeps that bearer-token identity path for project, conversation, message, and run-trigger routes. Health routes remain public.

Full run execution internals, queueing, SSE, retrieval, drafting, evaluation, repair, richer tenant authorization, frontend auth UX, recovery-code MFA UX, and worker job processing remain out of scope.
