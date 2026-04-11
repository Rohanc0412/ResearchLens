from datetime import UTC, datetime
from xml.etree import ElementTree

from researchlens.modules.retrieval.domain.candidate import (
    CanonicalIdentifiers,
    NormalizedSearchCandidate,
    QueryProvenance,
    SourceProvenance,
)
from researchlens.modules.retrieval.domain.query_plan import RetrievalQuery


def candidate(
    *,
    provider_name: str,
    provider_record_id: str | None,
    identifiers: CanonicalIdentifiers,
    title: str | None,
    authors: tuple[str, ...],
    year: int | None,
    source_type: str,
    abstract: str | None,
    full_text: str | None,
    landing_page_url: str | None,
    pdf_url: str | None,
    venue: str | None,
    citation_count: int | None,
    keywords: tuple[str, ...],
    query: RetrievalQuery,
    metadata: dict[str, object],
) -> NormalizedSearchCandidate:
    return NormalizedSearchCandidate(
        provider_name=provider_name,
        provider_record_id=provider_record_id,
        identifiers=identifiers.normalized(),
        title=title,
        authors=authors,
        year=year,
        source_type=source_type,
        abstract=abstract,
        full_text=full_text,
        landing_page_url=landing_page_url,
        pdf_url=pdf_url,
        venue=venue,
        citation_count=citation_count,
        keywords=keywords,
        retrieved_at=datetime.now(tz=UTC),
        provider_metadata=metadata,
        provenance=(SourceProvenance(provider_name, provider_record_id),),
        query_provenance=QueryProvenance(
            query.query,
            query.intent.value,
            query.target_section,
        ),
    )


def element_text(entry: ElementTree.Element, path: str, ns: dict[str, str]) -> str | None:
    element = entry.find(path, ns)
    return element.text.strip() if element is not None and element.text else None


def string(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def integer(value: object) -> int | None:
    if not isinstance(value, int | str):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def year(value: str | None) -> int | None:
    return integer(value[:4]) if value else None


def clean_doi(value: str | None) -> str | None:
    return value.removeprefix("https://doi.org/") if value else None


def strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in (string(raw) for raw in value) if item is not None)
