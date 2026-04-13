# ResearchLens

ResearchLens is a quality-first monorepo for conversation-driven research runs. The current product includes auth, projects, conversations, canonical run lifecycle, streaming progress, evidence inspection, evaluation and repair reads, and artifact export/download flows.

The cloned `ResearchLens` directory is the project root. Do not create a nested `ResearchLens/ResearchLens/` folder.

## Repository layout

- `apps/api`: thin FastAPI entrypoint that wires the installed backend package.
- `apps/worker`: thin worker process for DB-backed queue polling and LangGraph run execution.
- `apps/web`: Vite React app with `app/`, `pages/`, `widgets/`, `features/`, `entities/`, and `shared/`.
- `packages/backend`: installable Python backend package, migrations, and backend tests.
- `packages/api_client`: generated TypeScript client built from the backend OpenAPI schema.
- `packages/ui`: generic shared React components.
- `docs`: architecture, configuration, testing docs, ADRs, and phase reports.

## Install

Expected tools:

- Python 3.12+
- `uv`
- Node.js
- Corepack-managed `pnpm`

Install everything:

```bash
python -m uv sync --all-packages --group dev
corepack pnpm install
```

## Key commands

Backend:

```bash
python -m uv run --package researchlens-api python -m researchlens_api.main
python -m uv run --package researchlens-worker python -m researchlens_worker.main
python -m uv run --package researchlens-backend pytest packages/backend/tests
python -m uv run --package researchlens-backend alembic -c packages/backend/alembic.ini upgrade head
```

Frontend:

```bash
corepack pnpm --filter @researchlens/api-client run generate
corepack pnpm --filter web dev --host 127.0.0.1 --port 4173
corepack pnpm --filter web lint
corepack pnpm --filter web typecheck
corepack pnpm --filter web test
corepack pnpm --filter web build
corepack pnpm --filter web exec playwright test
```

Workspace CI-equivalent:

```bash
python -m uv run --package researchlens-backend ruff check .
python -m uv run --package researchlens-backend mypy apps/api/src apps/worker/src packages/backend/src packages/backend/tests
python -m uv run --package researchlens-backend lint-imports --config .importlinter
python -m uv run --package researchlens-backend pytest packages/backend/tests
corepack pnpm lint
corepack pnpm typecheck
corepack pnpm test
corepack pnpm build
```

## Current HTTP surface

- `/healthz`, `/health`
- `/auth/*`
- `/projects/*`
- `/projects/{project_id}/conversations`
- `/conversations/{conversation_id}/*`
- `/runs/{run_id}`, `/runs/{run_id}/events`, `/runs/{run_id}/cancel`, `/runs/{run_id}/retry`
- `/runs/{run_id}/evaluation`, `/runs/{run_id}/evaluation/issues`
- `/runs/{run_id}/evidence`, `/runs/{run_id}/evidence/sections/{section_id}`
- `/evidence/chunks/{chunk_id}`, `/evidence/sources/{source_id}`
- `/runs/{run_id}/artifacts`, `/artifacts/{artifact_id}`, `/artifacts/{artifact_id}/download`

## Frontend status

Phase 11 rebuilds the browser app around the current backend contracts:

- generated API client from backend OpenAPI
- refresh-cookie-aware auth restore, logout, password reset, and MFA flows
- project and conversation shell with persisted messages
- canonical run start from conversations and SSE progress streaming with `Last-Event-ID`
- evidence snippet and source detail views
- artifact list, preview for text-like outputs, and real download behavior
- Vitest coverage for auth/session and SSE logic plus Playwright E2E for major flows

See [docs/architecture/frontend-architecture.md](/c:/projects/ResearchLens/docs/architecture/frontend-architecture.md), [docs/architecture/streaming-protocol.md](/c:/projects/ResearchLens/docs/architecture/streaming-protocol.md), and [docs/phase_reports/phase_11_completion.md](/c:/projects/ResearchLens/docs/phase_reports/phase_11_completion.md) for the current implementation details.
