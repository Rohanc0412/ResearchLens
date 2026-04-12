# Phase 8 Completion

## Scope

Phase 8 implemented evaluation only: claim extraction, RAGAS-backed faithfulness scoring, structured issues, metrics, persistence, graph integration, queryable reads, tests, and docs. Repair execution and frontend work remain out of scope.

## Implemented

- Added `researchlens.modules.evaluation` with domain, application, infrastructure, orchestration, and presentation layers.
- Added append-only evaluation pass persistence plus per-section result, claim, and issue tables.
- Added strict verdict, issue type, severity, scoring, and repair-trigger policies.
- Added RAGAS faithfulness integration using the shared OpenAI LLM settings and ResearchLens-owned output contracts.
- Added evaluation subgraph after drafting and before finalization.
- Added summary and issue read routes: `GET /runs/{run_id}/evaluation` and `GET /runs/{run_id}/evaluation/issues`.

## Schema Summary

Migration `20260412_0007_phase_8_evaluation.py` creates:

- `evaluation_passes`
- `evaluation_section_results`
- `evaluation_claims`
- `evaluation_issues`

Structured issue rows include section metadata, claim metadata, verdict, issue type, severity, rationale, cited chunk ids, supported chunk ids, allowed chunk ids, and repair hints.

## Lifecycle

Evaluation writes progress events and a compact checkpoint through existing runs bridges. Evaluation issues are product findings and do not fail an otherwise successful run. Operational evaluator failures fail the stage and preserve the existing retry rule: failures at or after drafting restart from `draft`.

## Repair Policy

Repair is recommended only when faithfulness is below 70 percent or any claim is `contradicted`. Maximum repairs per section is fixed at 1. Phase 8 persists the signal and issue inputs but does not execute repair.

## Tests And Docs

Added evaluation unit and integration tests for scoring, repair policy, DTO strictness, citation validation, claim-output normalization, persistence, queries, and subgraph execution. Updated architecture, lifecycle, settings, streaming, README, and module-boundary documentation, and added `docs/architecture/evaluation-module.md`.

## Open Risks

- Phase 9 must consume `evaluation_section_results.repair_attempt_count` and enforce the single-repair policy.
- Provider-cost and timeout tuning may need adjustment after real workload observation.
