# Test Strategy

ResearchLens verification now spans backend, generated client, frontend logic, and browser flows.

## Backend

Backend coverage still includes:

- architecture and import-boundary checks
- packaging guardrails for installed-package imports, absolute Python imports, and no `PYTHONPATH` or `sys.path.insert` hacks
- backend module layer checks for required `domain`, `application`, `infrastructure`, and `presentation` directories, with `orchestration` limited to staged run modules
- naming and file-size checks for production Python and TypeScript source files
- startup smoke tests
- migrations
- module unit tests
- API contracts
- integration tests for auth, projects, conversations, runs, evaluation, repair, evidence, and artifacts

## Frontend

Phase 11 adds:

- unit tests for SSE parsing and reconnect behavior
- auth/session behavior tests around bootstrap restore and `401` refresh retry
- route/page tests for login-mode rendering
- Playwright E2E for:
  - login
  - session restore
  - logout
  - auth-expiration redirect
  - conversation and message flow
  - run progress and artifact navigation
  - artifact download

E2E uses deterministic API fixtures while running the real routed frontend, generated client, and browser transport code.

## CI-equivalent command set

```bash
python -m uv run --package researchlens-backend ruff check .
python -m uv run --package researchlens-backend mypy apps/api/src apps/worker/src packages/backend/src packages/backend/tests
python -m uv run --package researchlens-backend lint-imports --config .importlinter
python -m uv run --package researchlens-backend pytest packages/backend/tests
corepack pnpm lint
corepack pnpm typecheck
corepack pnpm test
corepack pnpm build
corepack pnpm --filter web exec playwright test
```
