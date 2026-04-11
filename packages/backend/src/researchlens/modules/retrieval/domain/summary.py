from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RetrievalSummary:
    run_id: UUID
    outline_sections: int
    planned_queries: int
    normalized_candidates: int
    selected_sources: int
    ingested_sources: int
    fallback_used: bool
    provider_failures: tuple[str, ...] = ()
    planning_warnings: tuple[str, ...] = ()
