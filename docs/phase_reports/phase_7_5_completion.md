# Phase 7.5 Completion

## Graph architecture summary

- `runs` now owns a top-level LangGraph for each research run.
- The graph flow is `load_run_context -> restore_or_initialize_graph_state -> maybe_resume_from_checkpoint -> retrieval_subgraph -> drafting_subgraph -> finalize_run`.
- Retrieval and drafting execute only through graph-native orchestration entrypoints.
- Worker composition now assembles a LangGraph run orchestrator instead of a stage-controller shell.

## Graph state summary

- Canonical graph state lives in `runs.orchestration.state`.
- State is reference-oriented: run ids, queue refs, retry/cancel flags, checkpoint refs, request text, and compact retrieval/drafting summaries.
- Durable outputs remain in lifecycle tables plus retrieval and drafting persistence tables.

## Event bridge summary

- `runs.orchestration.event_bridge` maps graph progress into persisted `run_events`.
- Event keys remain dedupe-safe with the existing `attempt-{retry_count}:...` convention.
- JSON and SSE delivery still read the same persisted event stream.

## Checkpoint bridge summary

- `runs.orchestration.checkpoint_bridge` maps graph checkpoints into persisted `run_checkpoints`.
- Checkpoint keys remain dedupe-safe with the existing `attempt-{retry_count}:...` convention.
- Stage-local graph checkpoints also include lifecycle resume metadata so restore stays deterministic from the latest checkpoint.

## Cancel and resume mapping summary

- Cancel remains cooperative and runs through the existing `cancel_requested_at` durable state.
- Retry before drafting still resumes from the latest successful checkpoint.
- Retry at or after drafting still restarts from `draft`.
- Worker restart resume still uses the latest durable checkpoint and run state.

## Legacy execution code removed

- removed `runs.application.stage_execution_controller`
- removed `runs.application.stage_progress_writers`
- removed `retrieval.orchestration.retrieval_stage_orchestrator`
- removed `drafting.orchestration.drafting_stage_orchestrator`
- removed the worker-owned `ResearchStageExecutionController` path that directly called retrieval and drafting outside a graph

## Tests added or updated

- added unit tests for graph state restore, event-key mapping, checkpoint-key mapping, and cancel interrupt mapping
- updated drafting integration tests to execute through the drafting subgraph
- updated worker lifecycle tests to preserve durable lifecycle intent under the new orchestrator boundary
- added regression coverage asserting the legacy stage-controller files are gone
- full backend suite passes: `175 passed`

## Docs added or updated

- updated `docs/architecture/system-overview.md`
- updated `docs/architecture/module-boundaries.md`
- updated `docs/architecture/run-lifecycle.md`
- updated `docs/architecture/streaming-protocol.md`
- added `docs/architecture/langgraph-runtime.md`
- added `docs/architecture/research-run-graph.md`
- updated `docs/configuration/settings.md`
- added `docs/adr/2026-04-12-langgraph-first-research-run-orchestration.md`

## Open questions for Phase 8

- whether evaluation should be a single subgraph or split into scoring and policy-routing subgraphs
- how repair retries should publish user-facing progress without becoming event-noisy
- whether evaluation and repair need graph interrupts beyond the current stage-boundary cancel model
