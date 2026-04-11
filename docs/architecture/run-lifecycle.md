# Run Lifecycle

Phase 5 moves run lifecycle ownership into `researchlens.modules.runs`.

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
- Project deletion behavior is unchanged in Phase 5, so run history retention across project deletes remains a later-phase risk.

## Queue and lease semantics

- Queue storage is DB-backed through `run_queue_items`.
- At most one active queue item exists per run at a time.
- Claim order is oldest available item first.
- Claimed work receives a lease token plus `lease_expires_at`.
- If a worker dies before completion, another worker may reclaim the item after lease expiry.
- Queue claims stop once `QUEUE_MAX_ATTEMPTS` is reached; exhausted items are no longer reclaimed for additional processing attempts in Phase 5.
- PostgreSQL uses row-locking claim semantics; SQLite tests use a conditional-update fallback that preserves correctness.

## Checkpoints

- Checkpoints are append-only stage-boundary records in `run_checkpoints`.
- Each checkpoint includes `run_id`, `stage`, `checkpoint_key`, `payload_json`, `summary_json`, and `created_at`.
- `checkpoint_key` is unique per run so retries or replays of the same logical boundary return the existing checkpoint instead of writing duplicates.
- Phase 5 checkpoint payloads stay small and focus on completed stages, next stage, attempt number, and retry count.

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
- Stage boundary transaction: update `current_stage`, write checkpoint, append `checkpoint.written` and `stage.completed`
- Cancel transaction: record `cancel_requested_at`, append `cancel.requested`, and if still queued finalize `canceled`
- Retry transaction: validate failed status, increment `retry_count`, clear retryable failure fields, choose retry floor, transition `failed -> queued`, re-enqueue, append `retry.requested`
