# Evaluation Module

`researchlens.modules.evaluation` owns the pipeline and targeted repair-reevaluation checks.

## Responsibilities

- load drafted section text and each section's allowed evidence pack
- create append-only `evaluation_passes` history with `scope=pipeline`
- extract atomic claims and normalize verdicts into ResearchLens-owned contracts
- score per-section RAGAS faithfulness and persist `ragas_faithfulness_pct`
- persist per-section results, extracted claims, and structured issues
- compute report metrics as deterministic rollups from section results
- expose latest summary, issue listing, and repair-candidate queries
- support a targeted `scope=repair_reevaluation` pass for repaired sections only

## RAGAS Runtime

Production evaluation uses the shared OpenAI-backed LLM settings and the RAGAS `Faithfulness` metric through an evaluation infrastructure adapter. RAGAS outputs are not the durable public contract; the module maps them into `EvaluationSummary`, `EvaluationSectionResult`, `EvaluatedClaimPayload`, and `EvaluationIssuePayload`.

Claim extraction and verdict normalization use the shared structured generation boundary with strict Pydantic parsing and bounded retries. Citation ids are validated against the section evidence pack only; evaluation never widens a section to all run evidence.

## Issue Schema

Persisted issue rows include run/pass/section identifiers, section title/order, optional claim identifiers, verdict, issue type, severity, message, rationale, cited chunk ids, supported chunk ids, allowed chunk ids, repair hint, and timestamps. These rows are the Phase 9 repair input, not an opaque JSON summary.

## Repair Signal

The pipeline pass persists `repair_recommended` only when:

- `ragas_faithfulness_pct < 70`
- or any claim verdict is `contradicted`

Other issue types do not trigger repair when faithfulness is at least 70 and no claim is contradicted. The durable repair hook is `repair_attempt_count` on section results plus `max_repairs_per_section=1` in the application policy. Phase 9 increments that count at the durable start of a repair attempt.

## Graph Integration

The top-level graph is:

`load_run_context -> restore_or_initialize_graph_state -> maybe_resume_from_checkpoint -> retrieval_subgraph -> drafting_subgraph -> evaluation_subgraph -> repair_subgraph -> maybe_reevaluate_repaired_sections_subgraph -> finalize_run`

Evaluation emits concise progress events and compact checkpoints through the runs-owned bridges. The targeted repair-reevaluation pass uses the same evaluator/provider path, filters to changed section ids, persists linked section results with `repair_result_id`, and does not create a second repair loop. Content-quality findings do not fail the run; provider/runtime/persistence failures do.
