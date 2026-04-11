# Phase 6 Completion Report

## Provider Contract Summary

Retrieval defines an internal `SearchProvider` port with `search` and `fetch_content` methods. Provider adapters return `NormalizedSearchCandidate` objects with canonical identifiers, metadata, query provenance, and provider provenance. Paper Search MCP is the primary provider; PubMed, Europe PMC, OpenAlex, and arXiv are configured as direct fallback providers.

## Retrieval Architecture Summary

The retrieval module is decomposed into domain, application, infrastructure, and orchestration layers. Pure domain logic owns canonical identifier handling, deduplication, ranking, and diversification. Application logic owns provider fan-out and query planning. Infrastructure owns provider adapters, ingestion helpers, embedding batching, and SQLAlchemy rows/repositories. Orchestration coordinates the run-stage boundary without importing runs.

## Outline-First Retrieval Summary

The stage creates a bounded retrieval outline before query planning, then generates global and section-aware deterministic query plans. The outline remains retrieval-focused and is not used for drafting.

## LLM Abstraction/Config Summary

Shared LLM code lives under `researchlens.shared.llm`. Retrieval depends on provider-agnostic ports. The active adapter is OpenAI with the default model `gpt-5-nano`; provider, model, base URL, timeouts, output limit, temperature, and enablement flags are typed settings.

## Embedding Abstraction/Config Summary

Shared embedding code lives under `researchlens.shared.embeddings`. Retrieval depends on provider-agnostic embedding ports and infrastructure batching helpers. The active embedding model default is `text-embedding-3-small`; provider, model, base URL, cache flag, batch size, concurrency, timeout, and API key are typed settings.

## Concurrency/Performance Strategy Summary

Provider searches use async fan-out with a bounded semaphore. Direct fallback providers are run concurrently when fallback is triggered. Embedding batching utilities preserve input order and bound concurrent batch calls. Retrieval settings define provider limits, candidate caps, selected-source caps, enrichment concurrency, and stage soft budget values.

## Persistence Summary

The Phase 6 migration adds retrieval source, snapshot, chunk, embedding cache, and run-source linkage tables. The ingestion repository stores selected sources, skips duplicate snapshots by content hash, chunks selected content, records embedding cache rows by text hash/model, stores vectors when an embedding client is configured, and links sources to the run.

## Unresolved Recall/Precision Tradeoffs

- Provider adapters are HTTP-capable and contract-tested offline, but production deployment still needs real endpoint configuration for Paper Search MCP and operational rate-limit tuning.
- Ranking now supports embedding rerank through the embedding port, but retrieval quality tuning remains a Phase 7 task once live corpus/provider behavior is available.
- Enrichment routing is implemented, but provider-specific full-text depth will need expansion as later evidence phases define precision/recall targets.
