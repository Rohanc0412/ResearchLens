# ADR 0004: Retrieval Persistence and Failure Policy

## Status

Accepted

## Context

Phase 6 needs enough persistence for later evidence phases without building the full evidence UI or export flows. It also needs explicit fallback behavior without silent provider failures.

## Decision

Retrieval persistence is owned by the retrieval infrastructure package and stores sources, snapshots, chunks, chunk embeddings, and run-to-source linkage. Content hashes and text hashes drive idempotency for snapshots and embeddings.

Provider fallback is fail-visible. MCP failures and direct-provider failures are recorded in retrieval summaries and run events. Zero useful candidates fails the stage clearly. Deterministic planning fallbacks are documented and emitted as planning warnings.

## Consequences

Retries can restart from the retrieval stage boundary and rely on persisted content hashes to reduce duplicate work. Later evidence and artifact phases can build on retrieval-owned rows without introducing a dumping-ground corpus package.
