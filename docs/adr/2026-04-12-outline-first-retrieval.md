# ADR 0001: Outline-First Retrieval Planning

## Status

Accepted

## Context

Phase 6 retrieval quality depends on planning around the shape of the report instead of starting provider search directly from the raw user question.

## Decision

ResearchLens generates a bounded retrieval outline before query planning. The outline includes a title and ordered retrieval-focused sections with goals and evidence themes. Query planning consumes that outline and produces global and section-aware retrieval queries.

The outline is not a drafting artifact. Full report drafting, evaluation, and repair remain out of Phase 6 scope.

## Consequences

Retrieval can diversify by section and intent earlier in the pipeline. If LLM query planning fails, the system falls back to deterministic query planning and emits run-visible warnings. Outline generation failure uses the documented deterministic minimal outline path so the stage remains explicit and testable.
