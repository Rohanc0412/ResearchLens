# System Overview

ResearchLens is a phased monorepo rebuild. Phase 5 extends the Phase 4 foundation with a dedicated `runs` slice for lifecycle state, queueing, events, checkpoints, retry/cancel flows, worker polling, and streaming.

## Monorepo structure

The repository is split into `apps/` and `packages/` so deployment-facing entrypoints stay separate from reusable code:

- `apps/api` is the HTTP/API surface. It remains thin and owns only composition: logging bootstrap, exception handlers, middleware, health routes, auth/projects router wiring, and request-scoped runtime assembly.
- `apps/worker` is the background execution process. It stays thin and owns only composition plus queue polling cadence; run lifecycle policy remains in the installed backend package.
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

## Phase 5 status

The backend currently includes:

- shared logging with request ID and tenant context
- async DB engine, session, and transaction primitives
- lazy runtime health checks for DB connectivity and schema readiness
- one migration-backed `projects` module with create, list, get, update, and delete
- one migration-backed `auth` module with register, login, refresh, logout, `/auth/me`, password reset request/confirm, and TOTP MFA enrollment/challenge/disable
- one migration-backed `conversations` module with project-scoped conversation CRUD and message persistence
- one migration-backed `runs` module with canonical create/get/cancel/retry/event routes, DB-backed queue leasing, append-only events and checkpoints, and retry/cancel lifecycle rules
- worker polling that reuses the same shared foundation and executes the placeholder run stage pipeline

Phase 3 replaced the Phase 2 `bootstrap_actor` protected-route identity path with auth-backed bearer token resolution. Phase 5 keeps that bearer-token identity path for project, conversation, message, and run lifecycle routes. Health routes remain public.

Retrieval, drafting, evaluation, repair, export business logic, richer tenant authorization, frontend auth UX, and recovery-code MFA UX remain out of scope. Phase 5 proves the lifecycle shell only; later phases plug real pipeline work into the existing run backbone.
