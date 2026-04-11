from datetime import UTC, datetime

from researchlens.modules.retrieval.application.ports import (
    FetchedSourceContent,
    ProviderSearchRequest,
)
from researchlens.modules.retrieval.domain.candidate import (
    CanonicalIdentifiers,
    NormalizedSearchCandidate,
    QueryProvenance,
    SourceProvenance,
)


class FakeSearchProvider:
    def __init__(
        self,
        *,
        provider_name: str,
        titles: list[str] | None = None,
        fail: bool = False,
    ) -> None:
        self._provider_name = provider_name
        self._titles = titles or []
        self._fail = fail

    @property
    def provider_name(self) -> str:
        return self._provider_name

    async def search(self, request: ProviderSearchRequest) -> list[NormalizedSearchCandidate]:
        if self._fail:
            raise RuntimeError(f"{self._provider_name} failed")
        return [
            NormalizedSearchCandidate(
                provider_name=self._provider_name,
                provider_record_id=f"{self._provider_name}-{index}",
                identifiers=CanonicalIdentifiers(url=f"https://example.test/{title}"),
                title=title,
                authors=(),
                year=None,
                source_type="paper",
                abstract=None,
                full_text=None,
                landing_page_url=None,
                pdf_url=None,
                venue=None,
                citation_count=None,
                keywords=(),
                retrieved_at=datetime.now(tz=UTC),
                provider_metadata={},
                provenance=(
                    SourceProvenance(
                        provider_name=self._provider_name,
                        provider_record_id=f"{self._provider_name}-{index}",
                    ),
                ),
                query_provenance=QueryProvenance(
                    source_query=request.query.query,
                    intent=request.query.intent.value,
                    target_section=request.query.target_section,
                ),
            )
            for index, title in enumerate(self._titles[: request.max_results])
        ]

    async def fetch_content(
        self,
        candidate: NormalizedSearchCandidate,
    ) -> FetchedSourceContent | None:
        return FetchedSourceContent(
            full_text=candidate.full_text,
            abstract=candidate.abstract,
            landing_page_url=candidate.landing_page_url,
            pdf_url=candidate.pdf_url,
        )
