# ADR 0002: Retrieval Provider Contract

## Status

Accepted

## Context

Phase 6 uses Paper Search MCP as the primary search provider and PubMed, Europe PMC, OpenAlex, and arXiv as direct fallback providers. Those providers expose different identifiers, metadata, and content capabilities.

## Decision

Retrieval providers implement the internal `SearchProvider` port. Provider-specific HTTP mapping stays in retrieval infrastructure, and application logic consumes normalized candidates with canonical identifiers, provenance, query intent, and optional richer content fields.

Paper Search MCP runs first. Direct providers run in parallel only when MCP fails, times out, or yields fewer than the configured normalized candidate threshold. Provider failures are preserved in retrieval results and surfaced through run events.

## Consequences

Provider differences are normalized at adapter boundaries. Deduplication, ranking, diversification, and ingestion remain independent from provider SDKs and HTTP payload shapes. Offline fake providers are explicitly config-driven for local and test execution.
