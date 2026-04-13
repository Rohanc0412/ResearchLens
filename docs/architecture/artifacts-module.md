# Artifacts Module

The `researchlens.modules.artifacts` module owns report export and artifact downloads.

It persists:

- `artifacts`: metadata for stored artifact bytes, including kind, filename, media type, storage backend/key, size, checksum, metadata, and manifest linkage
- `artifact_manifests`: durable queryable report manifest rows with final section refs, source refs, citation map, evaluation/repair provenance, warnings, and the full manifest JSON
- `artifact_download_records`: append-only download audit rows

Phase 10 ships one real storage provider: `FilesystemArtifactStore`. It stores bytes under `STORAGE_LOCAL_ARTIFACT_ROOT`, records SHA-256 and byte size, rejects absolute/path-traversal storage keys, and is used by both export and download paths.

Export generates:

- final report markdown
- report manifest JSON

PDF export remains out of scope because no reliable CI-friendly renderer is currently wired.

The export subgraph is graph-native and runs before finalization. It calls application use cases for bundle loading, citation resolution, manifest rendering, markdown rendering, storage, and persistence. It writes compact checkpoints and emits concise export events through runs-owned bridges.
