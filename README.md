# ResearchLens

ResearchLens is being rebuilt as a quality-first monorepo for research workflow orchestration, evidence handling, drafting, evaluation, and artifact production. This repository is the phased reconstruction, not a direct continuation of the previous code layout.

Phase 4 adds project detail/update flows plus the first real `conversations` slice for conversations, messages, and minimal run-trigger intent recording on top of the Phase 3 auth-backed protected routes. Full run execution, assistant generation, retrieval, drafting, evaluation, repair, and broader frontend rebuild work remain deferred.

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

Python 3.12, the `uv` Python module or CLI, Node.js, and Corepack-provided `pnpm` are the expected tools.

```bash
make install
```

Equivalent commands:

```bash
python -m uv sync --all-packages --group dev
corepack pnpm install
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

The root `package.json` uses recursive pnpm workspace scripts for JavaScript and TypeScript tasks. Python commands run from installed-package context through `python -m uv`.

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
python -m uv run --package researchlens-api python -m researchlens_api.main
python -m uv run --package researchlens-worker python -m researchlens_worker.main
python -m uv run --package researchlens-backend pytest packages/backend/tests
python -m uv run --package researchlens-backend alembic -c packages/backend/alembic.ini upgrade head
```

The API entrypoint stays composition-only and wires health, auth, projects, conversations, messages, and run-trigger routers from the backend package. Worker queue processing and later research workflow modules remain deferred.
