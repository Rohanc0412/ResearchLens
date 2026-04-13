# System Overview

ResearchLens is a phased monorepo rebuild. The current backend builds on the Phase 5 durable run lifecycle, the Phase 6 retrieval foundation, the Phase 7 drafting module, and the Phase 8 evaluation module while keeping LangGraph as the only research-run orchestrator.

## Monorepo structure

The repository is split into `apps/` and `packages/` so deployment-facing entrypoints stay separate from reusable code:

- `apps/api` is the HTTP/API surface. It remains thin and owns only composition: logging bootstrap, exception handlers, middleware, health routes, auth/projects router wiring, and request-scoped runtime assembly.
- `apps/worker` is the background execution process. It stays thin and owns only composition plus queue polling cadence; run lifecycle policy remains in the installed backend package.
- `apps/web` is the browser client workspace. It currently remains a thin placeholder shell while preserving the disciplined frontend folder structure.

- `packages/backend` is the canonical installable Python package for backend modules, typed config, shared DB runtime, migrations, and backend tests.
- `packages/api_client` is reserved for generated TypeScript client artifacts.
- `packages/ui` is reserved for generic frontend UI components shared across apps.

## Why split apps and packages

This separation keeps runtime entrypoints thin and dependency direction explicit:

- apps depend on packages
- packages do not depend on app-local folders
- reusable code remains installable and testable
- Docker, CI, pytest, and Alembic use the same installed-package boundaries as local development

## Current status

The backend currently includes:

- shared logging with request ID and tenant context
- async DB engine, session, and transaction primitives
- lazy runtime health checks for DB connectivity and schema readiness
- one migration-backed `projects` module with create, list, get, update, and delete
- one migration-backed `auth` module with register, login, refresh, logout, `/auth/me`, password reset request/confirm, and TOTP MFA enrollment/challenge/disable
- one migration-backed `conversations` module with project-scoped conversation CRUD and message persistence
- one migration-backed `runs` module with canonical create/get/cancel/retry/event routes, DB-backed queue leasing, append-only events and checkpoints, and retry/cancel lifecycle rules
- one migration-backed `retrieval` module with provider-agnostic search contracts, offline fake-provider mode by default, Paper Search MCP plus PubMed/Europe PMC/OpenAlex/arXiv when external fetch is enabled, pure ranking/diversification policies, source/snapshot/chunk/embedding-cache tables, and thin retrieval orchestration
- one migration-backed `drafting` module with drafting-owned section/evidence/draft/report persistence, strict citation-token validation against retrieval chunks, bounded concurrent section drafting, and deterministic markdown report assembly
- one migration-backed `evaluation` module with append-only passes, per-section RAGAS faithfulness, persisted claims, repair-ready issue rows, deterministic summary rollups, and auth-protected read routes
- provider-agnostic shared LLM and embedding ports with OpenAI adapters isolated under `shared/llm/providers` and `shared/embeddings/providers`
- worker polling that reuses the same shared foundation and executes the research run through a top-level LangGraph owned by `runs`
- graph-native retrieval orchestration that still delegates business logic to retrieval application/domain/infrastructure code
- graph-native drafting orchestration that still delegates evidence-pack, citation, and report-assembly policy to drafting-owned code
- graph-native evaluation orchestration that still delegates claim, scoring, repair-threshold, RAGAS, and persistence work to evaluation-owned code
- graph-native repair orchestration that consumes persisted evaluation issues, updates canonical drafted sections, and invokes targeted reevaluation for changed sections only
- a runs-owned graph bridge that maps graph progress into persisted Phase 5 events, checkpoints, cancel handling, retry floors, and final status transitions

Phase 3 replaced the Phase 2 `bootstrap_actor` protected-route identity path with auth-backed bearer token resolution. Phase 5 keeps that bearer-token identity path for project, conversation, message, and run lifecycle routes. Health routes remain public.

Research runs are now split cleanly:

- `runs` owns queue leasing, lifecycle state, run events, checkpoints, cancel/retry/resume rules, and the top-level graph
- LangGraph owns execution flow between retrieval, drafting, and evaluation
- `retrieval` owns retrieval business logic, providers, ranking, enrichment, ingestion, and persistence
- `drafting` owns evidence-pack derivation, section drafting, citation validation, and report assembly
- `evaluation` owns claim extraction, claim verdict normalization, RAGAS faithfulness scoring, issue persistence, summary rollups, and repair recommendation signals
- `repair` owns repair selection, prompt construction, provider-backed section repair, validated fallback edits, repair persistence, canonical section updates, read models, and repair-to-reevaluation linkage

There is no remaining non-graph research-run execution shell in production code.

Repair execution, export polish, richer tenant authorization, frontend auth UX, and recovery-code MFA UX remain out of scope. Retrieval and drafting stay backend-internal; evaluation exposes summary and issue read APIs only.
