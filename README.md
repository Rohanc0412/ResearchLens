# ResearchLens

ResearchLens is being rebuilt as a quality-first monorepo for research workflow orchestration, evidence handling, drafting, evaluation, and artifact production. This repository is the phased reconstruction, not a direct continuation of the previous code layout.

Phase 1 focuses on installed-package execution, unified backend dependencies, typed settings, minimal DB and Alembic wiring, and architecture enforcement. Business features are still intentionally deferred.

The cloned `ResearchLens` directory is the project root. Do not create a nested `ResearchLens/ResearchLens/` folder. All repo paths are relative to the current root.

## Repository layout

- `apps/api`: bootstrap-only ASGI entrypoint for the future API service.
- `apps/worker`: bootstrap-only worker runtime scaffold.
- `apps/web`: minimal frontend scaffold with disciplined feature/entity/widget structure.
- `packages/backend`: installable backend package with shared primitives and module placeholders.
- `packages/api_client`: placeholder for generated API client artifacts.
- `packages/ui`: placeholder UI package for shared frontend components.
- `docs`: architecture, phase workflow, ADR guidance, and phase reports.
- `infra`: development-only Docker, compose, and GitHub automation support docs.
- `scripts`: focused repository scripts only.

## Install

Python 3.12, `uv`, Node.js, and `pnpm` are the expected tools.

```bash
make install
```

Equivalent commands:

```bash
uv sync --all-packages --group dev
pnpm install
```

## Common commands

```bash
make lint
make typecheck
make architecture
make test
make db-upgrade
make build
make format
```

The root `package.json` uses Turbo to orchestrate JavaScript and TypeScript workspace tasks. Python commands run from installed-package context through `uv`.

## Placeholder services

Start the API scaffold:

```bash
make dev-api
```

Start the worker scaffold:

```bash
make dev-worker
```

Start the web scaffold:

```bash
make dev-web
```

Installed-package equivalents:

```bash
uv run --package researchlens-api python -m researchlens_api.main
uv run --package researchlens-worker python -m researchlens_worker.main
uv run --package researchlens-backend pytest packages/backend/tests
uv run --package researchlens-backend alembic -c packages/backend/alembic.ini upgrade head
```

These entrypoints remain intentionally bootstrap-only. No business endpoints, auth flow, queue processing, or persistence logic has been implemented beyond the minimal startup and migration wiring required for Phase 1.
