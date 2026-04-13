# Phase 10 Completion

## Evidence architecture

Added `researchlens.modules.evidence` as a read-focused composition module with strict DTOs, thin routes, application use cases, and SQL query adapters. It reads from durable retrieval, drafting, evaluation, repair, run, and artifact tables without duplicating source-of-truth evidence rows.

## Artifact and export architecture

Added `researchlens.modules.artifacts` with artifact domain models, application use cases for citation resolution, manifest building, markdown rendering, artifact persistence, artifact listing/detail/downloads, infrastructure rows/repositories, a local filesystem artifact store, and a graph-native export subgraph.

## Final canonical section-content rule

Export and evidence inspection use repaired text/summary only when the latest successful repair result changed that section. Otherwise they use the persisted drafting section text/summary. Reevaluation validates changed repaired sections but does not produce prose.

## Storage provider summary

Phase 10 supports only the real local filesystem provider. `STORAGE_MODE=local` and `STORAGE_LOCAL_ARTIFACT_ROOT` configure it. The provider writes real bytes, reads downloads from disk, records byte size and SHA-256, and rejects path traversal.

## Export graph integration

The top-level run graph now routes to `artifact_export_subgraph` before `finalize_run`. Export writes through runs-owned event/checkpoint bridges and uses stable per-run artifact kinds for idempotent resume/retry behavior.

## Manifest and download-record summary

The migration adds `artifacts`, `artifact_manifests`, and `artifact_download_records`. Manifests preserve final section refs, source refs, citation mappings, evaluation/repair provenance, artifact IDs, checksums via artifact rows, and warnings. Downloads append durable records with tenant, artifact, run, actor, request ID, user-agent, and timestamp.

## Tests and docs updated

Added unit coverage for citation resolution, filesystem storage, and idempotent artifact persistence. Added integration coverage for export from persisted retrieval/drafting outputs, evidence summary composition, and download record persistence. Updated architecture, settings, streaming, lifecycle, README, and testing docs, and added dedicated evidence/artifacts architecture docs.

## Open risks for Phase 11

The frontend still needs evidence and artifact UX. Source metadata is only as rich as upstream retrieval providers populate it. PDF export remains out of scope until a reliable CI-friendly renderer is selected.
