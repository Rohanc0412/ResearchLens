# System Overview

ResearchLens is a phased monorepo rebuild. Phase 0 establishes repository shape, installable packaging, tooling, and guardrails before any business workflows are reintroduced.

## Monorepo structure

The repository is split into `apps/` and `packages/` so deployment-facing entrypoints stay separate from reusable code:

- `apps/api` is the future HTTP/API surface. In Phase 0 it provides only a bootstrap-safe health check and application factory.
- `apps/worker` is the future background execution process. In Phase 0 it exposes only a minimal runtime description.
- `apps/web` is the future browser client. In Phase 0 it provides only a placeholder shell and disciplined folder structure.

- `packages/backend` is the installable Python package for backend modules and shared cross-cutting primitives.
- `packages/api_client` is reserved for generated TypeScript client artifacts.
- `packages/ui` is reserved for generic frontend UI components shared across apps.

## Why split apps and packages

This separation keeps runtime entrypoints thin and dependency direction explicit:

- apps depend on packages
- packages do not depend on app-local folders
- reusable code remains installable and testable
- Docker and CI can use the same package boundaries as local development

## Phase 0 status

Business features are intentionally deferred. There are no real API workflows, auth flows, persistence models, queue integrations, or provider adapters in this phase.

