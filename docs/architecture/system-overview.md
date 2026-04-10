# System Overview

ResearchLens is a phased monorepo rebuild. Phase 2 extends the Phase 1 package and boundary foundation with shared backend runtime primitives and one real `projects` vertical slice.

## Monorepo structure

The repository is split into `apps/` and `packages/` so deployment-facing entrypoints stay separate from reusable code:

- `apps/api` is the HTTP/API surface. In Phase 2 it remains thin and owns only composition: logging bootstrap, exception handlers, middleware, health routes, and router wiring.
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

## Phase 2 status

Phase 2 keeps the scope intentionally small:

- shared logging with request ID and tenant context
- async DB engine, session, and transaction primitives
- lazy runtime health checks for DB connectivity and schema readiness
- one migration-backed `projects` module with create, list, rename, and delete
- worker bootstrap that reuses the same shared foundation

Auth, runs, retrieval, LLM stages, conversations, and worker job processing remain out of scope.
