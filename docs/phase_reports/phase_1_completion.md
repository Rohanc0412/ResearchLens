# Phase 1 Completion Report

## Phase title

Packaging, dependency unification, typed config, and architecture enforcement

## Scope restatement

Phase 1 made `packages/backend` the canonical installed backend package, unified Python dependency declaration around `pyproject.toml` and `uv.lock`, added typed grouped settings with validation, introduced minimal shared DB and Alembic wiring, moved backend verification into installed-package tests, and enforced architecture boundaries in CI. Business features remained out of scope.

## Deliverables completed

- Canonical backend runtime dependencies in `packages/backend/pyproject.toml`
- Installed-package API and worker execution paths
- Typed grouped settings under `researchlens.shared.config`
- Explicit startup validation for unsafe or incompatible settings combinations
- Minimal shared DB runtime bootstrap under `researchlens.shared.db`
- Alembic configuration and migration environment importing `researchlens` directly
- Backend-owned smoke, config, Alembic, architecture, and path-hack regression tests under `packages/backend/tests`
- `import-linter` contracts plus CI architecture checks
- Updated Docker, compose, Make, Just, and CI commands to run from installed-package context
- Configuration and architecture documentation updates

## Validation status

- Backend package remains rooted at `packages/backend/src/researchlens`
- API and worker entrypoints remain thin in `researchlens_api` and `researchlens_worker`
- Bootstrap `/healthz` route remains present
- No `PYTHONPATH`, `sys.path.insert`, or `prepend_sys_path` is used in runtime config files
- Installed-package commands are wired as the canonical execution path
- Verified with `uv lock`, `uv sync --all-packages --group dev`, `ruff`, `mypy`, `pytest`, `lint-imports`, direct Alembic upgrade, direct worker startup, and an isolated-port API health probe
- Workspace lockfiles now exist as `uv.lock` and `pnpm-lock.yaml`

## Deviations

- Phase 1 keeps the health route as the only API route and does not connect to the database on startup by default.
- SQLite remains the local-safe default database URL for lightweight startup and tests, while production validation rejects SQLite.
- Module cross-dependency discipline is enforced through backend regression tests in addition to `import-linter`, because app entrypoint and cross-module rules are easier to express precisely there.
- Local root Turbo execution through `corepack pnpm` depends on a usable `pnpm` binary on `PATH`; package-level frontend checks were verified directly in this shell, and CI is configured with explicit pnpm setup.

## Open decisions for Phase 2

- Decide the first business module to implement on top of the new layer structure
- Decide the concrete initial ORM models and migration revisions
- Decide queue backend details beyond Phase 1 placeholders
- Decide observability implementation details beyond typed config shape
- Decide which provider integrations enter the codebase first
