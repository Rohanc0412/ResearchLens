from researchlens.modules.retrieval.domain.candidate import (
    CanonicalIdentifiers,
    NormalizedSearchCandidate,
)

DIRECT_PROVIDER_TIE_BREAK = ("pubmed", "europe_pmc", "openalex", "arxiv")


def deduplicate_candidates(
    candidates: list[NormalizedSearchCandidate],
) -> list[NormalizedSearchCandidate]:
    by_key: dict[str, NormalizedSearchCandidate] = {}
    order: list[str] = []
    for candidate in candidates:
        normalized = candidate.normalized()
        key = normalized.identifiers.canonical_key(normalized.title)
        if key not in by_key:
            by_key[key] = normalized
            order.append(key)
        else:
            by_key[key] = merge_candidates(by_key[key], normalized)
    return [by_key[key] for key in order]


def merge_candidates(
    left: NormalizedSearchCandidate,
    right: NormalizedSearchCandidate,
) -> NormalizedSearchCandidate:
    return NormalizedSearchCandidate(
        provider_name=_preferred_provider(left.provider_name, right.provider_name),
        provider_record_id=left.provider_record_id or right.provider_record_id,
        identifiers=_merge_identifiers(left.identifiers, right.identifiers),
        title=_richer_text(left.title, right.title),
        authors=left.authors if len(left.authors) >= len(right.authors) else right.authors,
        year=left.year or right.year,
        source_type=left.source_type or right.source_type,
        abstract=_richer_text(left.abstract, right.abstract),
        full_text=_richer_text(left.full_text, right.full_text),
        landing_page_url=left.landing_page_url or right.landing_page_url,
        pdf_url=left.pdf_url or right.pdf_url,
        venue=left.venue or right.venue,
        citation_count=max(left.citation_count or 0, right.citation_count or 0) or None,
        keywords=tuple(dict.fromkeys([*left.keywords, *right.keywords])),
        retrieved_at=min(left.retrieved_at, right.retrieved_at),
        provider_metadata={**left.provider_metadata, **right.provider_metadata},
        provenance=tuple(dict.fromkeys([*left.provenance, *right.provenance])),
        query_provenance=left.query_provenance,
    )


def _merge_identifiers(
    left: CanonicalIdentifiers,
    right: CanonicalIdentifiers,
) -> CanonicalIdentifiers:
    return CanonicalIdentifiers(
        doi=left.doi or right.doi,
        pmid=left.pmid or right.pmid,
        pmcid=left.pmcid or right.pmcid,
        arxiv_id=left.arxiv_id or right.arxiv_id,
        openalex_id=left.openalex_id or right.openalex_id,
        url=left.url or right.url,
    ).normalized()


def _richer_text(left: str | None, right: str | None) -> str | None:
    if not left:
        return right
    if not right:
        return left
    return right if len(right) > len(left) else left


def _preferred_provider(left: str, right: str) -> str:
    if left == "paper_search_mcp":
        return right if right in DIRECT_PROVIDER_TIE_BREAK else left
    if right == "paper_search_mcp":
        return left
    left_rank = DIRECT_PROVIDER_TIE_BREAK.index(left) if left in DIRECT_PROVIDER_TIE_BREAK else 99
    right_rank = (
        DIRECT_PROVIDER_TIE_BREAK.index(right) if right in DIRECT_PROVIDER_TIE_BREAK else 99
    )
    return left if left_rank <= right_rank else right
