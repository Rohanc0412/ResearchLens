from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from researchlens.modules.retrieval.domain.candidate import NormalizedSearchCandidate
from researchlens.modules.retrieval.domain.query_plan import RetrievalQuery
from researchlens.modules.retrieval.domain.ranking_policy import RankedCandidate
from researchlens.modules.retrieval.domain.retrieval_outline import RetrievalOutline


@dataclass(frozen=True, slots=True)
class ProviderSearchRequest:
    query: RetrievalQuery
    max_results: int


@dataclass(frozen=True, slots=True)
class FetchedSourceContent:
    full_text: str | None
    abstract: str | None
    landing_page_url: str | None
    pdf_url: str | None


@dataclass(frozen=True, slots=True)
class ProviderFailure:
    provider_name: str
    operation: str
    reason: str


class SearchProvider(Protocol):
    @property
    def provider_name(self) -> str: ...

    async def search(self, request: ProviderSearchRequest) -> list[NormalizedSearchCandidate]: ...

    async def fetch_content(
        self,
        candidate: NormalizedSearchCandidate,
    ) -> FetchedSourceContent | None: ...


class RetrievalIngestionRepository(Protocol):
    async def persist_selected_sources(
        self,
        *,
        run_id: UUID,
        outline: RetrievalOutline,
        selected: list[RankedCandidate],
    ) -> int: ...
