# Research Run Graph

The Phase 10 top-level research-run graph is:

`load_run_context`
-> `restore_or_initialize_graph_state`
-> `maybe_resume_from_checkpoint`
-> `retrieval_subgraph`
-> `drafting_subgraph`
-> `evaluation_subgraph`
-> `repair_subgraph` when the Phase 8 repair policy selects sections
-> `maybe_reevaluate_repaired_sections_subgraph` when repair changed sections
-> `artifact_export_subgraph`
-> `finalize_run`

## Node roles

- `load_run_context`: loads the run row, latest checkpoint, and original request text from durable stores.
- `restore_or_initialize_graph_state`: builds canonical graph state from durable lifecycle data.
- `maybe_resume_from_checkpoint`: marks the run `running` when needed and preserves resume intent.
- `retrieval_subgraph`: executes outline, planning, search, ranking, enrichment, ingestion, and retrieval checkpoint/event writes.
- `drafting_subgraph`: executes evidence-pack preparation, section drafting, report assembly, and drafting checkpoint/event writes.
- `evaluation_subgraph`: loads drafted sections and section-scoped evidence, creates an append-only evaluation pass, evaluates sections with bounded concurrency, persists claims/issues/section results, rolls up metrics, and writes an evaluation checkpoint.
- `repair_subgraph`: selects only sections with `repair_attempt_count < 1` and either faithfulness below 70 percent or a contradicted claim, consumes persisted issue details, runs provider-backed structured repair, applies conservative validated fallback edits when safe, updates canonical draft rows, and writes repair persistence/events/checkpoints.
- `maybe_reevaluate_repaired_sections_subgraph`: runs evaluation in `scope=repair_reevaluation` only for sections whose canonical text changed during repair or fallback, links the reevaluation pass back to repair results, and never routes back into repair.
- `artifact_export_subgraph`: deterministically assembles final section text, resolves persisted chunk/source citations, writes markdown and manifest artifacts through the local filesystem artifact store, persists artifact metadata and a compact export checkpoint, and does not perform creative rewriting.
- `finalize_run`: maps graph completion or cooperative cancel into the existing terminal lifecycle mutations.

## Stage boundaries

- `runs` still owns `stage.started`, `checkpoint.written`, and `stage.completed` lifecycle boundaries.
- Retrieval, drafting, evaluation, repair, targeted reevaluation, and export emit additional human-readable progress events and compact stage-local checkpoints through runs-owned bridges.
- The graph never becomes the durable source of truth; it is only the execution-flow layer.
- Evaluation findings are product quality outputs. Unsupported or weak claims can set `repair_recommended=true`; repair and targeted reevaluation make one controlled attempt to improve changed sections, and unresolved-after-repair findings still do not fail an otherwise operationally successful run.
- Export failures occur after drafting/evaluation/repair in lifecycle terms. Export uses stable per-run artifact kinds so retry or resume overwrites the same logical artifacts rather than creating duplicate report files.
