from dataclasses import dataclass, replace
from datetime import datetime
from hashlib import sha256


@dataclass(frozen=True, slots=True)
class CanonicalIdentifiers:
    doi: str | None = None
    pmid: str | None = None
    pmcid: str | None = None
    arxiv_id: str | None = None
    openalex_id: str | None = None
    url: str | None = None

    def normalized(self) -> "CanonicalIdentifiers":
        return CanonicalIdentifiers(
            doi=_lower(self.doi),
            pmid=_compact(self.pmid),
            pmcid=_upper(self.pmcid),
            arxiv_id=_lower(self.arxiv_id),
            openalex_id=_upper(self.openalex_id),
            url=_lower(self.url),
        )

    def canonical_key(self, title: str | None) -> str:
        values = self.normalized()
        for name in ("doi", "pmid", "pmcid", "arxiv_id", "openalex_id", "url"):
            value = getattr(values, name)
            if value:
                return f"{name}:{value}"
        stable_title = " ".join((title or "").casefold().split())
        return f"title:{sha256(stable_title.encode('utf-8')).hexdigest()}"


@dataclass(frozen=True, slots=True)
class QueryProvenance:
    source_query: str
    intent: str
    target_section: str | None = None


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    provider_name: str
    provider_record_id: str | None


@dataclass(frozen=True, slots=True)
class NormalizedSearchCandidate:
    provider_name: str
    provider_record_id: str | None
    identifiers: CanonicalIdentifiers
    title: str | None
    authors: tuple[str, ...]
    year: int | None
    source_type: str
    abstract: str | None
    full_text: str | None
    landing_page_url: str | None
    pdf_url: str | None
    venue: str | None
    citation_count: int | None
    keywords: tuple[str, ...]
    retrieved_at: datetime
    provider_metadata: dict[str, object]
    provenance: tuple[SourceProvenance, ...]
    query_provenance: QueryProvenance

    def normalized(self) -> "NormalizedSearchCandidate":
        return replace(self, identifiers=self.identifiers.normalized(), title=_clean(self.title))


def _lower(value: str | None) -> str | None:
    return value.strip().casefold() if value and value.strip() else None


def _upper(value: str | None) -> str | None:
    return value.strip().upper() if value and value.strip() else None


def _compact(value: str | None) -> str | None:
    return "".join(value.split()) if value and value.strip() else None


def _clean(value: str | None) -> str | None:
    return " ".join(value.split()) if value and value.strip() else None
