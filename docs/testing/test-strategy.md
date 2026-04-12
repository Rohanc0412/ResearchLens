# Test Strategy

Backend tests cover module boundaries, smoke startup, migrations, unit policies, repositories, API contracts, and integration-stage behavior.

Phase 8 adds focused evaluation coverage for:

- verdict scoring and report rollups
- exact repair trigger policy and `max_repairs_per_section=1`
- strict DTO and structured claim output contracts
- citation-to-allowed-evidence validation
- evaluation persistence and latest-summary/issue/repair-candidate queries
- evaluation subgraph execution with successful quality findings
- migration creation of evaluation tables

The local CI-equivalent command set remains:

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
