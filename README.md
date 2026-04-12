# ResearchLens

ResearchLens is being rebuilt as a quality-first monorepo for research workflow orchestration, evidence handling, drafting, evaluation, and artifact production. This repository is the phased reconstruction, not a direct continuation of the previous code layout.

The current backend includes auth, projects, conversations, run lifecycle, DB-backed queueing, SSE progress streaming, internal retrieval, internal drafting, and Phase 8 evaluation. Retrieval performs outline-first planning, provider search, candidate normalization, ranking, diversification, source ingestion, and run-source persistence through the worker. Drafting prepares section evidence packs from persisted retrieval chunks, calls the real shared LLM path, persists per-section outputs, and assembles a deterministic markdown report draft. Evaluation runs after drafting through LangGraph, uses RAGAS-backed faithfulness scoring plus structured claim verdicts, persists queryable issues, and marks repair recommendations without executing repair. Repair execution, export polish, recovery-code MFA UX, richer tenant authorization, and the broader frontend rebuild remain deferred.

The cloned `ResearchLens` directory is the project root. Do not create a nested `ResearchLens/ResearchLens/` folder. All repo paths are relative to the current root.

## Repository layout

- `apps/api`: thin ASGI entrypoint that wires logging, middleware, health, auth, projects, conversations, messages, and runs routes from the backend package.
- `apps/worker`: thin worker process that polls the DB-backed run queue and executes the retrieval, drafting, and evaluation pipeline.
- `apps/web`: frontend scaffold with disciplined page/widget/feature/entity/shared structure and a placeholder shell.
- `packages/backend`: installable backend package with shared primitives, migrations, tests, and modular business slices.
- `packages/api_client`: TypeScript workspace package reserved for generated API client artifacts.
- `packages/ui`: shared React UI workspace package with generic reusable components.
- `docs`: architecture, phase workflow, ADR guidance, and phase reports.
- `infra`: development-only Docker, compose, and GitHub automation support docs.
- `scripts`: focused repository scripts only.

## Install

Python 3.12, `uv` as either a Python module or CLI, Node.js, and Corepack-provided `pnpm` are the expected tools.

Use Doppler-backed runtime injection for any command that needs secrets. `.env.example` is a reference template only.

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
make doppler-dev-api
make doppler-dev-worker
make doppler-test-backend
```

The root `package.json` uses recursive pnpm workspace scripts for JavaScript and TypeScript tasks. Local Make/Just commands run Python from installed-package context through `python -m uv`; CI uses the `uv` CLI after `astral-sh/setup-uv`.

## Local services

Start the API with Doppler:

```bash
make doppler-dev-api
```

Start the worker with Doppler:

```bash
make doppler-dev-worker
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

Current HTTP surface:

- `/healthz` and `/health`
- `/auth/*`
- `/projects/*`
- `/projects/{project_id}/conversations`
- `/conversations/{conversation_id}/*` for conversation, message, and run creation flows
- `/runs/{run_id}`, `/runs/{run_id}/events`, `/runs/{run_id}/cancel`, and `/runs/{run_id}/retry`
- `/runs/{run_id}/evaluation` and `/runs/{run_id}/evaluation/issues`

The API entrypoint stays composition-only and wires health, auth, projects, conversations, messages, runs, and evaluation read routers from the backend package. The worker entrypoint stays composition-only and delegates queue polling plus retrieval/drafting/evaluation-aware run processing to backend composition helpers and installed backend modules.
