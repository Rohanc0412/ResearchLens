# Run Lifecycle

Phase 5 moved run lifecycle ownership into `researchlens.modules.runs`. Phase 6 plugs the real retrieval stage into that lifecycle without moving retrieval policy into the runs module. Phase 7 plugs the real drafting stage into the same lifecycle boundary.

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

## Stage sequence

- The canonical run-stage sequence is `retrieve -> draft -> evaluate -> export`.
- The worker executes real stage logic for `retrieve` and `draft`.
- `evaluate` and `export` remain reserved lifecycle stages and currently flow through the fallback sleep controller.
- Legacy enum members such as `ingest`, `outline`, `evidence_pack`, `validate`, `repair`, and `factcheck` still exist for display compatibility, but they are not part of the active execution sequence.

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
- If a worker dies after a completed stage checkpoint, replay resumes from the checkpoint's `next_stage`.
- Duplicate stage-completed events are prevented with per-run `event_key` dedupe.
- If `cancel_requested_at` is set before resume, the worker stops at the next safe boundary and finalizes `canceled`.

## Retry resume-floor rule

- If failure happened before drafting started, retry resumes from the latest successful checkpoint.
- If failure happened at or after drafting, including later `evaluate` or `export` stages, retry restarts from `draft`.
- This rule is intentional and favors downstream coherence over aggressive partial replay.

## Transaction boundaries

- API create-run transaction: validate conversation, enforce idempotency, create the run, transition `created -> queued`, append initial events, enqueue queue work
- Worker claim transaction: claim queue item and write lease metadata
- Worker run-start transaction: transition `queued -> running` and append `run.running`
- Retrieval stage transactions: write retrieval run events and checkpoints through the existing runs event/checkpoint stores, and persist selected sources through retrieval-owned repositories
- Drafting stage transactions: load retrieval-linked chunks through a drafting-owned input port, persist drafting-owned section preparation rows, draft sections through the shared LLM boundary, persist section drafts, and upsert the assembled report draft
- Stage boundary transaction: update `current_stage`, write checkpoint, append `checkpoint.written` and `stage.completed`
- Cancel transaction: record `cancel_requested_at`, append `cancel.requested`, and if still queued finalize `canceled`
- Retry transaction: validate failed status, increment `retry_count`, clear retryable failure fields, choose retry floor, transition `failed -> queued`, re-enqueue, append `retry.requested`

## Retrieval stage behavior

The retrieve stage now executes outline-first retrieval before the generic stage-completed mutation runs. The worker composition root creates a retrieval stage controller that:

- generates a bounded retrieval outline before query planning
- plans queries from the outline
- uses offline fake providers by default for local and test execution
- searches Paper Search MCP first when `RETRIEVAL_ALLOW_EXTERNAL_FETCH=true`
- runs direct fallback providers when primary search fails or returns too few deduped candidates
- normalizes, deduplicates, ranks, diversifies, and persists selected sources
- emits concise retrieval progress events and dedupe-safe retrieval checkpoints

The current StageExecutionController hook receives the run and stage. The retrieval controller reads the original request text from the existing `run.created` event payload so retrieval planning can still start from the user research question without changing the Phase 5 run table contract.

## Drafting stage behavior

The draft stage now executes after retrieval and before the generic stage-completed mutation runs. The worker composition root assembles a drafting-aware stage controller that:

- derives an ordered drafting section plan from persisted retrieval section targeting
- builds section-level evidence packs from persisted retrieval chunks without widening access to all run evidence
- renders deterministic section prompts outside orchestration code
- calls the real shared OpenAI-backed LLM path for structured section outputs
- validates citation tokens against the allowed chunk ids before persistence
- persists section outputs independently and assembles the report from persisted section rows in deterministic order

Evidence-pack preparation and section drafting are concurrent with bounded fan-out. Section-draft persistence remains intentionally sequential inside a single DB session so retry safety and transaction correctness stay deterministic. Continuity summaries are persisted with each section draft, but the current prompt flow does not yet feed prior section summaries into later prompts so the stage can stay fully parallel.
