# Phase 5 Completion Report

## Phase title

Run lifecycle, queueing, events, streaming, checkpoints, idempotency

## Scope restatement

Phase 5 implemented the operational run backbone only: dedicated run lifecycle ownership, DB-backed queue leasing, worker polling, run events, checkpoints, cancel/retry flows, SSE/JSON event delivery, idempotent run creation, retry resume-floor handling, tests, and lifecycle/streaming docs. Retrieval, drafting, evaluation, repair, export business logic, provider integrations, and the broad frontend rebuild stayed out of scope.

## State machine summary

- Statuses: `created`, `queued`, `running`, `succeeded`, `failed`, `canceled`
- Persisted transition history now lives in `run_status_transitions`
- Compatibility `POST /conversations/{conversation_id}/run-triggers` now delegates to the runs create-use case instead of owning lifecycle state itself

## Checkpoint strategy summary

- Checkpoints are append-only, stage-boundary records in `run_checkpoints`
- Each checkpoint carries a unique `checkpoint_key` per run plus small summary/payload JSON
- Phase 5 checkpoint payloads record completed stages, next stage, retry count, and attempt metadata rather than fake content output

## Event protocol summary

- `run_events` is the per-run event store with monotonic `event_number`
- Event rows store snapshot status/stage, retry count, cancel flag, human-readable message, and optional payload
- Duplicate logical event writes are deduped with `event_key`
- JSON and SSE delivery share the same envelope and ordering rules
- SSE reconnect uses `Last-Event-ID` and replays only events with `event_number > Last-Event-ID`
- Terminal SSE streams close after the configured grace window once final events are committed

## Transaction boundary summary

- Create, cancel, retry, run-start, stage-boundary, and finalize operations each commit as explicit lifecycle boundaries
- State row updates, transition history, and event writes are grouped in the same logical transactions
- Queue claim and lease writes are committed independently from stage execution
- Queue claim attempts now honor `QUEUE_MAX_ATTEMPTS`, and the worker poll loop has an explicit graceful stop path

## Idempotency and resume summary

- Run creation idempotency is `(tenant_id, conversation_id, client_request_id)` when `client_request_id` is present
- Queue enqueueing preserves a single active queue item per run
- Event writes dedupe on `(run_id, event_key)`
- Checkpoints dedupe on `(run_id, checkpoint_key)`
- Resume uses the latest checkpoint plus run status and lease state; terminal runs no-op safely

## Retry resume-floor summary

- Failures before drafting resume from the latest successful checkpoint
- Failures at or after drafting restart from `draft`
- Retry preserves the same run id, increments `retry_count`, clears retryable failure fields, re-enqueues the run, and appends retry history/events

## Frontend streaming contract summary

- `POST /conversations/{conversation_id}/runs`
- `POST /conversations/{conversation_id}/run-triggers`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/events`
- `POST /runs/{run_id}/cancel`
- `POST /runs/{run_id}/retry`

Run summaries include `display_status`, `display_stage`, `can_stop`, `can_retry`, and `cancel_requested`. Event payloads are already frontend-ready for a later run progress widget and support `Last-Event-ID` reconnect.

## Tests added or updated

- Unit tests for transition legality, retry floor selection, stage validation, and strict DTO contracts
- Integration tests for create/idempotent replay, compatibility alias behavior, queued cancel, SSE reconnect replay, queue lease exclusivity, lease reclaim, retry before/after drafting, worker restart resume, running cancel handling, duplicate event/checkpoint dedupe, terminal SSE grace-window closure, max-attempt queue cutoff, and migration upgrade coverage
- Smoke tests for installed-package startup and explicit worker shutdown behavior
- Final verification reran the full backend suite, backend lint/typecheck/import-linter chain, and the workspace `pnpm` lint/typecheck/test/build chain

## Docs added or updated

- `README.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/module-boundaries.md`
- `docs/architecture/run-lifecycle.md`
- `docs/architecture/streaming-protocol.md`
- `docs/configuration/settings.md`
- `docs/phase_reports/phase_5_completion.md`

## Migrations

- `packages/backend/migrations/versions/20260410_0004_phase_5_runs.py`

## Risks to watch in retrieval and drafting phases

- Project deletion still cascades to runs because Phase 5 kept existing project deletion behavior unchanged; long-term historical retention remains a later design decision
- The worker pipeline is intentionally a placeholder stage shell. Later retrieval/drafting phases must plug real stage logic into the existing lifecycle boundaries rather than bypassing them
- Queue backoff and external broker replacement were deferred; Phase 5 only proves the DB-backed contract and recovery semantics

## Final verification status

- Packaging: no path hacks were introduced; installed-package imports remain intact for API startup, worker startup, pytest, and Alembic
- Architecture: the worker app no longer imports runs infrastructure types directly; worker composition is expressed through a protocol-safe boundary
- Lifecycle correctness: the running-cancel path was verified end to end after fixing terminal cancel finalization so cooperative stop completes as `canceled`, not `failed`
- CI-equivalent command set passed locally on April 10, 2026:
  - `python -m uv run --package researchlens-backend ruff check .`
  - `python -m uv run --package researchlens-backend mypy apps/api/src apps/worker/src packages/backend/src packages/backend/tests`
  - `python -m uv run --package researchlens-backend lint-imports --config .importlinter`
  - `python -m uv run --package researchlens-backend pytest packages/backend/tests`
  - `corepack pnpm lint`
  - `corepack pnpm typecheck`
  - `corepack pnpm test`
  - `corepack pnpm build`
