# ADR: LangGraph-First Research-Run Orchestration

Date: 2026-04-12

## Status

Accepted

## Context

Phase 5 introduced durable run lifecycle ownership in `runs`. Phase 6 added real retrieval logic. Phase 7 added real drafting logic. The worker still executed those stages through a legacy non-graph shell.

That shell created two problems:

- execution flow was not obviously owned by one orchestration model
- future evaluation and repair stages would have added more branching to the same legacy shell

## Decision

Research runs now execute only through a runs-owned LangGraph:

- `runs` owns the top-level graph
- `retrieval` exposes graph-native retrieval orchestration pieces
- `drafting` exposes graph-native drafting orchestration pieces
- lifecycle durability stays in the existing runs repositories, event store, checkpoint store, and transition rules
- the legacy non-graph research-run execution shell is removed

## Consequences

- cancel, retry, resume, SSE ordering, and dedupe rules continue to use the Phase 5 durability model
- retrieval and drafting business rules remain outside graph files
- worker composition stays thin and does not become a second orchestrator
- Phase 8 can add evaluation and repair as additional graph stages without replacing lifecycle ownership again
