# System Overview

ResearchLens is a phased monorepo rebuild. Phase 1 turns the backend into a real installed package with unified dependencies, typed settings, minimal DB and Alembic wiring, and enforceable architecture boundaries before feature work expands.

## Monorepo structure

The repository is split into `apps/` and `packages/` so deployment-facing entrypoints stay separate from reusable code:

- `apps/api` is the future HTTP/API surface. In Phase 0 it provides only a bootstrap-safe health check and application factory.
- `apps/worker` is the future background execution process. In Phase 1 it remains a thin runtime wrapper around installed backend configuration and DB bootstrap.
- `apps/web` is the future browser client. In Phase 0 it provides only a placeholder shell and disciplined folder structure.

- `packages/backend` is the canonical installable Python package for backend modules, typed config, shared DB bootstrap, migrations, and backend tests.
- `packages/api_client` is reserved for generated TypeScript client artifacts.
- `packages/ui` is reserved for generic frontend UI components shared across apps.

## Why split apps and packages

This separation keeps runtime entrypoints thin and dependency direction explicit:

- apps depend on packages
- packages do not depend on app-local folders
- reusable code remains installable and testable
- Docker, CI, pytest, and Alembic use the same installed-package boundaries as local development

## Phase 1 status

Business features are intentionally deferred. There are still no real API workflows, auth flows, persistence models, queue integrations, or provider adapters beyond the minimal typed configuration and DB bootstrap required to make installed-package execution and migrations work.
