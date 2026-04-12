# Research Run Graph

The Phase 8 top-level research-run graph is:

`load_run_context`
-> `restore_or_initialize_graph_state`
-> `maybe_resume_from_checkpoint`
-> `retrieval_subgraph`
-> `drafting_subgraph`
-> `evaluation_subgraph`
-> `finalize_run`

## Node roles

- `load_run_context`: loads the run row, latest checkpoint, and original request text from durable stores.
- `restore_or_initialize_graph_state`: builds canonical graph state from durable lifecycle data.
- `maybe_resume_from_checkpoint`: marks the run `running` when needed and preserves resume intent.
- `retrieval_subgraph`: executes outline, planning, search, ranking, enrichment, ingestion, and retrieval checkpoint/event writes.
- `drafting_subgraph`: executes evidence-pack preparation, section drafting, report assembly, and drafting checkpoint/event writes.
- `evaluation_subgraph`: loads drafted sections and section-scoped evidence, creates an append-only evaluation pass, evaluates sections with bounded concurrency, persists claims/issues/section results, rolls up metrics, and writes an evaluation checkpoint.
- `finalize_run`: maps graph completion or cooperative cancel into the existing terminal lifecycle mutations.

## Stage boundaries

- `runs` still owns `stage.started`, `checkpoint.written`, and `stage.completed` lifecycle boundaries.
- Retrieval, drafting, and evaluation subgraphs emit additional human-readable progress events and compact stage-local checkpoints through runs-owned bridges.
- The graph never becomes the durable source of truth; it is only the execution-flow layer.
- Evaluation findings are product quality outputs. Unsupported or weak claims can set `repair_recommended=true` while the run still reaches `succeeded`; only operational evaluator failures fail the stage/run.
