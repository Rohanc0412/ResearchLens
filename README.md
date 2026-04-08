# ResearchLens

ResearchLens is being rebuilt as a quality-first monorepo for research workflow orchestration, evidence handling, drafting, evaluation, and artifact production. This repository is the phased reconstruction, not a direct continuation of the previous code layout.

Phase 0 covers bootstrap and guardrails only. The goal is to establish a clean workspace, packaging, CI, documentation, and coding constraints before any business features are rebuilt.

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

Python 3.12, `uv`, Node.js, and `pnpm` are the expected Phase 0 tools.

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
make test
make build
make format
```

The root `package.json` uses Turbo to orchestrate JavaScript and TypeScript workspace tasks.

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

These entrypoints are intentionally bootstrap-only. No business endpoints, auth flow, queue processing, or persistence logic has been implemented in Phase 0.

