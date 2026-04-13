# Evidence Module

The `researchlens.modules.evidence` module is a read-focused inspection module.

It exposes:

- `GET /runs/{run_id}/evidence`
- `GET /runs/{run_id}/evidence/sections/{section_id}`
- `GET /evidence/chunks/{chunk_id}`
- `GET /evidence/sources/{source_id}`

The module composes data from existing durable tables: retrieval sources/snapshots/chunks/run links, drafting sections/drafts/evidence packs, evaluation passes/results/claims/issues, repair passes/results, and artifact metadata. It does not mirror those records into a second evidence table.

Section traces use the Phase 10 canonical final-content rule: a successful changed repair result wins; otherwise the drafting section draft is the final text. Reevaluation validates repaired sections but does not create prose.

Evidence SQL adapters live in infrastructure and intentionally avoid importing other modules' ORM rows to preserve module-boundary contracts.
