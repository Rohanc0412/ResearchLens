# Phase 7 Completion

## Drafting flow summary

Phase 7 adds a real `drafting` bounded context. The worker now runs retrieval first, then drafting. Drafting derives an ordered section plan from retrieval-linked section targeting, builds section-scoped evidence packs from persisted retrieval chunks, renders deterministic prompts, calls the shared OpenAI-backed LLM path for structured section outputs, validates citation tokens, persists per-section drafts, and assembles a deterministic markdown report draft. The final implementation keeps drafting read access to run and retrieval state behind a dedicated drafting input-reader port and keeps drafting-owned writes in a separate repository adapter.

## Evidence-pack rules

- citeable evidence uses persisted retrieval chunk ids
- evidence packs are section-scoped and persisted
- sections may cite only chunk ids in their own pack
- packs are deterministic by source rank, chunk index, and chunk id
- empty packs fail drafting explicitly
- no silent fallback to all run evidence exists

## Open questions for evaluation metrics

- how strict should sentence-level grounding checks become once evaluation exists
- whether continuity summaries should be consumed by later sections or remain output-only while drafting stays maximally concurrent
- whether later phases should normalize duplicate citation tokens or preserve writer output verbatim

## Real provider-backed drafting path

Drafting uses the real shared `researchlens.shared.llm` runtime path. The OpenAI adapter now also parses structured JSON from `output_text` when needed, so production drafting is not scaffold-only. The current worker wiring keeps retrieval offline by default unless `RETRIEVAL_ALLOW_EXTERNAL_FETCH=true`, but drafting itself always uses the real configured LLM provider path when enabled.

## Doppler-based secrets workflow

Runtime secrets are now expected to arrive through Doppler-backed environment injection. `.env.example` remains a reference-only shape file. README, settings docs, Make targets, and compose guidance now point developers to `doppler run -- ...` for API, worker, migration, and test commands.
