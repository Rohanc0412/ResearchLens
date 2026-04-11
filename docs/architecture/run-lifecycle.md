# Run Lifecycle

Phase 5 moved run lifecycle ownership into `researchlens.modules.runs`. Phase 6 plugs the real retrieval stage into that lifecycle without moving retrieval policy into the runs module.

## Statuses and transitions

- Statuses: `created`, `queued`, `running`, `succeeded`, `failed`, `canceled`
- Allowed transitions:
  - `created -> queued`
  - `created -> canceled`
  - `queued -> running`
  - `queued -> canceled`
  - `running -> succeeded`
  - `running -> failed`
  - `running -> canceled`
  - `failed -> queued`
- Same-state retries are treated as idempotent no-ops by the caller; illegal transitions raise a conflict error.

Every status-changing write persists the updated `runs` row, a `run_status_transitions` history row, and the matching `run_events` record(s) in the same logical transaction.

## Ownership and compatibility

- `POST /conversations/{conversation_id}/runs` is the canonical run creation route.
- `POST /conversations/{conversation_id}/run-triggers` remains as a compatibility alias only.
- The conversations module is no longer the lifecycle source of truth.
- Runs belong primarily to `project_id`; `conversation_id` is nullable and uses `ON DELETE SET NULL`.
- Project deletion still cascades through the current schema, so run history retention across project deletes remains a later-phase risk.

## Queue and lease semantics

- Queue storage is DB-backed through `run_queue_items`.
- At most one active queue item exists per run at a time.
- Claim order is oldest available item first.
- Claimed work receives a lease token plus `lease_expires_at`.
- If a worker dies before completion, another worker may reclaim the item after lease expiry.
- Queue claims stop once `QUEUE_MAX_ATTEMPTS` is reached; exhausted items are no longer reclaimed for additional processing attempts.
- PostgreSQL uses row-locking claim semantics; SQLite tests use a conditional-update fallback that preserves correctness.

## Checkpoints

- Checkpoints are append-only stage-boundary records in `run_checkpoints`.
- Each checkpoint includes `run_id`, `stage`, `checkpoint_key`, `payload_json`, `summary_json`, and `created_at`.
- `checkpoint_key` is unique per run so retries or replays of the same logical boundary return the existing checkpoint instead of writing duplicates.
- Phase 5 checkpoint payloads stay small and focus on completed stages, next stage, attempt number, and retry count.
- Phase 6 retrieval adds retrieval-specific checkpoints with compact outline/query/provider/selection summaries. Raw provider payloads and full source text are not stored in run checkpoints; source content lives in retrieval-owned persistence tables.

## Resume rules

- Resume uses the latest checkpoint together with current run status and the active queue lease state.
- Terminal runs no-op safely if reclaimed.
- If a worker dies after a completed stage checkpoint, replay resumes from the checkpoint’s `next_stage`.
- Duplicate stage-completed events are prevented with per-run `event_key` dedupe.
- If `cancel_requested_at` is set before resume, the worker stops at the next safe boundary and finalizes `canceled`.

## Retry resume-floor rule

- If failure happened before drafting started, retry resumes from the latest successful checkpoint.
- If failure happened at or after drafting, retry restarts from `draft`.
- This rule is intentional and favors downstream coherence over aggressive partial replay.

## Transaction boundaries

- API create-run transaction: validate conversation, enforce idempotency, create the run, transition `created -> queued`, append initial events, enqueue queue work
- Worker claim transaction: claim queue item and write lease metadata
- Worker run-start transaction: transition `queued -> running` and append `run.running`
- Retrieval stage transactions: write retrieval run events and checkpoints through the existing runs event/checkpoint stores, and persist selected sources through retrieval-owned repositories
- Stage boundary transaction: update `current_stage`, write checkpoint, append `checkpoint.written` and `stage.completed`
- Cancel transaction: record `cancel_requested_at`, append `cancel.requested`, and if still queued finalize `canceled`
- Retry transaction: validate failed status, increment `retry_count`, clear retryable failure fields, choose retry floor, transition `failed -> queued`, re-enqueue, append `retry.requested`

## Retrieval stage behavior

The retrieve stage now executes outline-first retrieval before the generic stage-completed mutation runs. The worker composition root creates a retrieval stage controller that:

- generates a bounded retrieval outline before query planning
- plans queries from the outline
- searches Paper Search MCP first
- runs direct fallback providers when primary search fails or returns too few deduped candidates
- normalizes, deduplicates, ranks, diversifies, and persists selected sources
- emits concise retrieval progress events and dedupe-safe retrieval checkpoints

The current StageExecutionController hook receives the run and stage. The retrieval controller reads the original request text from the existing `run.created` event payload so retrieval planning can still start from the user research question without changing the Phase 5 run table contract.
