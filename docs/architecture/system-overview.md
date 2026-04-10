# System Overview

ResearchLens is a phased monorepo rebuild. Phase 3 extends the Phase 2 package, runtime, and `projects` slice with a strict auth module and real auth-backed request identity.

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

## Phase 3 status

The backend currently includes:

- shared logging with request ID and tenant context
- async DB engine, session, and transaction primitives
- lazy runtime health checks for DB connectivity and schema readiness
- one migration-backed `projects` module with create, list, rename, and delete
- one migration-backed `auth` module with register, login, refresh, logout, `/auth/me`, password reset request/confirm, and TOTP MFA enrollment/challenge/disable
- worker bootstrap that reuses the same shared foundation

Phase 3 replaces the Phase 2 `bootstrap_actor` protected-route identity path with auth-backed bearer token resolution. Health routes remain public.

Runs, retrieval, LLM stages, conversations, frontend auth flows, recovery-code MFA UX, and worker job processing remain out of scope.
