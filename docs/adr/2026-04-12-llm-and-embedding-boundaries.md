# ADR 0003: LLM and Embedding Boundaries

## Status

Accepted

## Context

Phase 6 uses GPT-5 nano for outline and query planning, and OpenAI `text-embedding-3-small` for ranking and ingestion embeddings. These are separate responsibilities and should remain switchable.

## Decision

LLM configuration lives under `shared.llm`, and embedding configuration lives under `shared.embeddings`. Retrieval application code depends on provider-agnostic ports only. OpenAI request and response mapping lives inside provider adapter modules.

Embedding batching is implemented in shared embedding coordination code so retrieval application logic does not import retrieval infrastructure.

## Consequences

Changing LLM or embedding providers later requires adding an adapter and changing typed settings. Retrieval ranking, planning, ingestion, and orchestration do not need OpenAI-specific refactors.
