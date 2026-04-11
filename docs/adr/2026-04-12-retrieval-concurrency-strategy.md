# ADR 0005: Retrieval Concurrency Strategy

## Status

Accepted

## Context

The Phase 6 retrieval stage targets practical completion under three minutes for normal runs while using multiple network-bound providers and embedding calls.

## Decision

Provider search, direct fallback fan-out, enrichment fetches, and embedding batches use async execution with explicit concurrency limits from typed settings. Work is bounded by outline section count, query count, provider result count, rerank top-k, selected source count, enrichment concurrency, and embedding batch concurrency.

## Consequences

The retrieval stage favors bounded partial progress over unbounded recall. Slow or unhealthy providers are surfaced through run events and do not block successful providers once fallback and time-budget rules allow progress.
