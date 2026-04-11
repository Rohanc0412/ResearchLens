# ResearchLens

ResearchLens is being rebuilt as a quality-first monorepo for research workflow orchestration, evidence handling, drafting, evaluation, and artifact production. This repository is the phased reconstruction, not a direct continuation of the previous code layout.

The current backend includes auth, projects, conversations, run lifecycle, DB-backed queueing, SSE progress streaming, and an internal Phase 6 retrieval stage. Retrieval now performs outline-first planning, provider search, candidate normalization/ranking/diversification, source ingestion, and run-source persistence through the worker. Drafting, evaluation, repair, export business logic, recovery-code MFA UX, richer tenant authorization, and the broader frontend rebuild remain deferred.

The cloned `ResearchLens` directory is the project root. Do not create a nested `ResearchLens/ResearchLens/` folder. All repo paths are relative to the current root.

## Repository layout

- `apps/api`: thin ASGI entrypoint that wires logging, middleware, health, auth, projects, conversations, and runs routes from the backend package.
- `apps/worker`: thin worker process that polls the DB-backed run queue and executes the retrieval-aware run lifecycle pipeline.
- `apps/web`: frontend scaffold with disciplined page/widget/feature/entity/shared structure and a placeholder shell.
- `packages/backend`: installable backend package with shared primitives, migrations, tests, and modular business slices.
- `packages/api_client`: TypeScript workspace package reserved for generated API client artifacts.
- `packages/ui`: shared React UI workspace package with generic reusable components.
- `docs`: architecture, phase workflow, ADR guidance, and phase reports.
- `infra`: development-only Docker, compose, and GitHub automation support docs.
- `scripts`: focused repository scripts only.

## Install

Python 3.12, `uv` as either a Python module or CLI, Node.js, and Corepack-provided `pnpm` are the expected tools.

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

The root `package.json` uses recursive pnpm workspace scripts for JavaScript and TypeScript tasks. Local Make/Just commands run Python from installed-package context through `python -m uv`; CI uses the `uv` CLI after `astral-sh/setup-uv`.

## Local services

Start the API:

```bash
make dev-api
```

Start the worker:

```bash
make dev-worker
```

Start the web shell:

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

The API entrypoint stays composition-only and wires health, auth, projects, conversations, and runs routers from the backend package. The worker entrypoint stays composition-only and delegates queue polling and retrieval-aware run processing to backend composition helpers and installed backend modules.
