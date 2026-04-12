# Drafting Module

`researchlens.modules.drafting` is the Phase 7 bounded context responsible for turning persisted retrieval outputs into grounded draft text.

## Responsibilities

- derive an ordered drafting section plan from retrieval-linked section targeting
- build section-scoped evidence packs from persisted retrieval chunks
- render deterministic section prompts outside orchestration code
- call the shared provider-backed LLM boundary for structured section drafts
- validate citation tokens against allowed evidence before persistence
- persist section outputs independently
- assemble a deterministic markdown report from persisted section outputs

## Module shape

- `application` owns drafting DTOs, section brief preparation, prompt rendering, validation, report assembly, and the `RunDraftingStageUseCase`
- `domain` owns drafting entities plus citation-token parsing and invariants
- `infrastructure` is split between a drafting input reader that loads run and retrieval inputs through SQL and a drafting output repository that persists only drafting-owned rows
- `orchestration` owns the thin stage coordinator that emits run progress through runs-supplied protocols

Worker composition is the only place that assembles drafting together with runs and retrieval.

## Owned persistence

- `drafting_sections`: drafting-owned section plan rows
- `drafting_section_evidence`: allowed evidence membership per section
- `drafting_section_drafts`: validated per-section outputs
- `drafting_report_drafts`: deterministic assembled report draft

## Evidence-pack rules

- The citeable evidence unit is the persisted retrieval chunk id from `retrieval_source_chunks`.
- Every evidence item in a section pack must belong to the same tenant and same run.
- A section may cite only chunk ids explicitly present in its own evidence pack.
- There is no fallback from a section pack to "all run evidence".
- Empty evidence packs fail drafting explicitly.
- Evidence ordering is deterministic by retrieval source rank, then chunk index, then chunk id.

## Citation token policy

- Internal citation tokens use `[[chunk:<uuid>]]`.
- Tokens are validated before persistence.
- Tokens must reference existing allowed chunk ids for the target section.
- `section_summary` is continuity-only. It must not contain citations or introduce new facts.

## Continuity behavior

- Each section draft stores a short continuity summary for possible later-stage use.
- The current drafting prompt flow does not feed prior continuity summaries into subsequent sections.
- This is intentional so section drafting can remain fully parallel and deterministic in Phase 7.

## Concurrency

- evidence-pack preparation runs concurrently with bounded fan-out
- prompt preparation is deterministic and per-section
- provider-backed section drafting runs concurrently with bounded fan-out
- section-draft persistence remains sequential within one `AsyncSession` because concurrent writes inside the same transaction boundary are not safe
- report assembly is deterministic from persisted section rows in section order
