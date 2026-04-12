# Research Run Graph

The Phase 7.5 top-level research-run graph is:

`load_run_context`
-> `restore_or_initialize_graph_state`
-> `maybe_resume_from_checkpoint`
-> `retrieval_subgraph`
-> `drafting_subgraph`
-> `finalize_run`

## Node roles

- `load_run_context`: loads the run row, latest checkpoint, and original request text from durable stores.
- `restore_or_initialize_graph_state`: builds canonical graph state from durable lifecycle data.
- `maybe_resume_from_checkpoint`: marks the run `running` when needed and preserves resume intent.
- `retrieval_subgraph`: executes outline, planning, search, ranking, enrichment, ingestion, and retrieval checkpoint/event writes.
- `drafting_subgraph`: executes evidence-pack preparation, section drafting, report assembly, and drafting checkpoint/event writes.
- `finalize_run`: maps graph completion or cooperative cancel into the existing terminal lifecycle mutations.

## Stage boundaries

- `runs` still owns `stage.started`, `checkpoint.written`, and `stage.completed` lifecycle boundaries.
- Retrieval and drafting subgraphs emit additional human-readable progress events and compact stage-local checkpoints through runs-owned bridges.
- The graph never becomes the durable source of truth; it is only the execution-flow layer.
