# Phase 9 Completion

## Repair Architecture

Phase 9 adds `researchlens.modules.repair` with domain selection policy, application repair contracts, SQL persistence, graph runtime/subgraph, and thin read routes. The run graph now routes `evaluate -> repair -> targeted repair_reevaluation -> finalize` without adding a non-graph execution path.

## Repair Input Contract

Repair inputs are built from durable evaluation section results, persisted evaluation issues, canonical drafting section drafts, and section-scoped evidence rows. Inputs include tenant/run/section metadata, current text/summary, evaluation result ids, attempt counts, faithfulness/contradiction triggers, issue ids/details, claim metadata, cited/supported/allowed chunk ids, repair hints, and evidence refs.

## Provider-Backed Repair Path

Repair uses the existing shared structured LLM client. It builds strict prompts from actual issue details and allowed evidence, expects JSON with `section_id`, `revised_text`, `revised_summary`, `addressed_issue_ids`, `citations_used`, and `self_check`, and rejects wrong section ids, empty text, unknown issue ids, and disallowed citations.

## Fallback Edits

Fallback edits are deterministic and conservative. They only remove exact contradicted-claim sentence targets when the target is unique and safe. Ambiguous or missing targets persist as unresolved instead of pretending success.

## Targeted Reevaluation

Changed sections only are reevaluated through the evaluation module in `scope=repair_reevaluation`. The pass stores `repair_result_id` on section results, links repair results to the reevaluation pass, and never routes back into repair. Unresolved findings after the single repair attempt are persisted as quality outcomes, not operational run failures.

## Graph Routing

The active graph is `load_run_context -> restore_or_initialize_graph_state -> maybe_resume_from_checkpoint -> retrieval_subgraph -> drafting_subgraph -> evaluation_subgraph -> repair_subgraph -> maybe_reevaluate_repaired_sections_subgraph -> finalize_run`. Repair is skipped when no section meets the Phase 8 trigger policy. Targeted reevaluation is skipped when repair changed no sections.

## Persistence

Migration `20260413_0008_phase_9_repair.py` adds `repair_passes`, `repair_results`, `repair_fallback_edits`, and `evaluation_section_results.repair_result_id`. Repair persistence records eligible/attempted/skipped sections, issue ids used, actions, validation summaries, unresolved reasons, fallback edits, changed status, and reevaluation pass linkage.

## Events And Checkpoints

Repair emits `repair.started`, `repair.section_selected`, `repair.section_started`, section completion/fallback events, and `repair.completed`. Targeted reevaluation emits `repair.reevaluation_started` and `repair.reevaluation.completed` through the evaluation runtime. Checkpoints stay compact and reference repair pass ids, selected/changed/unresolved/skipped section ids, and routing summaries.

## Tests

Added focused repair unit tests for selection, prompt contents, output validation, and fallback precision. Existing architecture, migration, drafting/evaluation integration, and full backend pytest suites pass in the available environment.

## Docs

Updated the README, graph, lifecycle, evaluation, settings, and test-strategy docs, and added this repair-module architecture page.

## Open Risks For Phase 10

The local environment is missing `uv`, `lint_imports`, and installed `openai`/`ragas` packages for exact CI command parity. Export-stage product behavior remains reserved for later work.
