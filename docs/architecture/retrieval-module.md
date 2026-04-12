# Retrieval Module

Phase 6 introduces `researchlens.modules.retrieval` as an internal backend module. It currently has no public routes.

## Flow

Retrieval is outline-first:

1. Build a bounded retrieval outline.
2. Plan global and section-aware retrieval queries from the outline.
3. Search Paper Search MCP first.
4. If primary search fails, times out, or produces fewer than 5 normalized deduped candidates, run PubMed, Europe PMC, OpenAlex, and arXiv fallback providers in parallel.
5. Normalize and deduplicate candidates with identifier-first priority.
6. Rank candidates with lexical, recency, citation, and optional embedding score inputs.
7. Diversify selected candidates by intent/section bucket.
8. Persist selected source metadata, snapshots, chunks, embedding cache rows, and run-source links.

## Boundaries

- `domain`: canonical identifiers, normalized candidates, query plans, outline types, dedupe, ranking, and diversification.
- `application`: provider ports, deterministic query planning, provider fan-out, and retrieval stage use case.
- `infrastructure`: provider adapters, provider registry, ingestion helpers, embedding batching, and SQLAlchemy persistence.
- `orchestration`: thin stage coordinator that emits run events/checkpoints through protocols supplied by worker composition.

The runs module does not import retrieval. Worker composition owns the cross-module assembly.

## Provider modes

- `RETRIEVAL_ALLOW_EXTERNAL_FETCH=false` keeps the provider registry offline with deterministic fake providers for local development and tests.
- `RETRIEVAL_ALLOW_EXTERNAL_FETCH=true` enables the HTTP-backed provider registry with Paper Search MCP as primary and PubMed, Europe PMC, OpenAlex, and arXiv as direct fallbacks.
- The retrieval application and orchestration code do not change between those modes; only the infrastructure registry swaps implementations.

## Provider Contract

Providers implement `SearchProvider`:

- `provider_name`
- `search(request) -> list[NormalizedSearchCandidate]`
- `fetch_content(candidate) -> FetchedSourceContent | None`

Normalized candidates carry canonical identifiers, title/authors/year/source type, abstract/full text URLs, citation count, keywords, provider metadata, provider provenance, and query provenance. Provider failures are represented as `ProviderFailure` and surfaced through run events when stage orchestration emits provider progress.

The provider classes are HTTP-capable adapters with fixture and `httpx.MockTransport` contract tests so tests remain offline. When `RETRIEVAL_ALLOW_EXTERNAL_FETCH=false`, the provider registry uses explicit offline providers for local and test execution rather than making live calls.

## Persistence

The Phase 6 migration adds:

- `retrieval_sources`
- `retrieval_source_snapshots`
- `retrieval_source_chunks`
- `retrieval_chunk_embeddings`
- `run_retrieval_sources`

Snapshots dedupe by source and content hash. Embedding rows dedupe by text hash and model. Run-source links dedupe by run/source. When an embedding client is configured, ingestion stores generated chunk vectors; otherwise it records cache rows without vectors for offline execution.
