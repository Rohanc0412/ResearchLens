import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueryIntent:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", normalize_query_intent(self.value))


@dataclass(frozen=True, slots=True)
class RetrievalQuery:
    intent: QueryIntent
    query: str
    target_section: str | None = None


@dataclass(frozen=True, slots=True)
class QueryPlan:
    queries: tuple[RetrievalQuery, ...]


def normalize_query_intent(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return normalized or "general"
