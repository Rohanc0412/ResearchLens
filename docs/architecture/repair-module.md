# Repair Module

Phase 9 adds `researchlens.modules.repair` as the repair bounded context.

## Responsibilities

- build repair inputs from durable pipeline evaluation section results, issues, drafting section drafts, and section evidence packs
- select only sections with `repair_attempt_count < 1` and either faithfulness below 70 percent or a contradicted claim
- construct provider-backed structured repair prompts from persisted issue details and allowed evidence
- validate model output against section id, non-empty revised text, known issue ids, and allowed citation chunk ids
- apply deterministic fallback edits only when contradicted-claim targets are precise
- persist repair passes, section results, fallback edits, skip/unresolved statuses, and reevaluation links
- update canonical drafting section text and the assembled report draft after successful model repair or validated fallback
- expose minimal read routes at `GET /runs/{run_id}/repair` and `GET /runs/{run_id}/repair/sections`

## Attempt Boundary

The single repair attempt is consumed when `repair_results.status=attempting` is inserted and the source `evaluation_section_results.repair_attempt_count` is incremented. Sections with `repair_attempt_count >= 1` are persisted as `skipped_attempt_limit` when still repair-triggering and are not attempted again.

## Reevaluation

Targeted reevaluation is owned by the evaluation module and invoked after repair only when `changed_section_ids` is non-empty. It creates an append-only `evaluation_passes` row with `scope=repair_reevaluation`, filters the evaluation input to changed section ids, stores `repair_result_id` on reevaluation section results, links repair results to the reevaluation pass, and finalizes afterward without routing back into repair.
