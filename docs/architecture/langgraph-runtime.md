# LangGraph Runtime

Phase 8 keeps LangGraph as the only production orchestrator for research runs.

## Ownership split

- `runs` owns queue pickup, durable state transitions, persisted run events, persisted checkpoints, retry floors, cancel handling, and final status writes.
- LangGraph owns execution flow between durable boundaries.
- `retrieval`, `drafting`, and `evaluation` expose graph-native orchestration pieces, but they do not own top-level lifecycle durability.

## Runtime pieces

- `runs.orchestration.state` defines the canonical reference-oriented graph state.
- `runs.orchestration.runtime_bridge` loads durable run context and maps graph progress into the existing Phase 5 mutation layer.
- `runs.orchestration.event_bridge` writes dedupe-safe progress events into `run_events`.
- `runs.orchestration.checkpoint_bridge` writes dedupe-safe graph checkpoints into `run_checkpoints`.
- `runs.orchestration.graph` owns the top-level research-run graph.

## Durable mapping rules

- `run_events` remains the source for ordered JSON and SSE delivery.
- `run_checkpoints` remains the source for resume and retry floor evaluation.
- Stage-local graph checkpoints also carry `completed_stages` and `next_stage` so the latest checkpoint is always sufficient for restore.
- Graph state carries references and summaries only; retrieval sources, drafting evidence, section drafts, reports, evaluation passes, claims, section results, and issues still persist in their owning modules.

## Cancel and resume

- The graph checks cancel state at stage boundaries through runs-owned durable state.
- Queued or running cancel requests still finalize as `canceled`, never `failed`.
- Retry before drafting still resumes from the latest successful checkpoint.
- Retry at or after drafting still restarts from `draft`.
- Evaluation runs after drafting, so operational evaluation failures also retry from `draft`.
