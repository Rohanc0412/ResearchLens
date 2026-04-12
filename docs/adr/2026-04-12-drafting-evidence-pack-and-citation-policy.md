# ADR: Drafting Evidence-Pack And Citation Policy

## Status

Accepted

## Context

Phase 7 adds real report drafting on top of persisted retrieval outputs. The system needs a deterministic citeable evidence unit, explicit section-level evidence gating, and a citation syntax that is easy to validate before later evaluation and export phases exist.

## Decision

- Drafting uses persisted retrieval chunk ids from `retrieval_source_chunks` as the citeable evidence unit.
- Each drafting section gets its own persisted evidence membership set in `drafting_section_evidence`.
- Section text may cite only chunk ids explicitly present in that section's evidence pack.
- Internal citation tokens use `[[chunk:<uuid>]]`.
- Empty evidence packs fail drafting explicitly instead of silently allowing unsupported prose.
- Section summaries are continuity-only and are not treated as evidence.

## Consequences

- Drafting can validate evidence use before persistence.
- Retry and reassembly stay deterministic because section outputs are persisted independently.
- Later evaluation and export phases can build on stable chunk-linked citation tokens instead of reverse-engineering citations from free text.
