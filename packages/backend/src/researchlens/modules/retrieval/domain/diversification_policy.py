from collections import defaultdict

from researchlens.modules.retrieval.domain.ranking_policy import RankedCandidate


def diversify_candidates(
    ranked: list[RankedCandidate],
    *,
    max_selected: int,
    per_bucket_limit: int,
) -> list[RankedCandidate]:
    selected: list[RankedCandidate] = []
    bucket_counts: dict[str, int] = defaultdict(int)
    for item in ranked:
        bucket = _bucket(item)
        if bucket_counts[bucket] < per_bucket_limit:
            selected.append(item)
            bucket_counts[bucket] += 1
        if len(selected) >= max_selected:
            return selected
    seen = {item.candidate.identifiers.canonical_key(item.candidate.title) for item in selected}
    for item in ranked:
        key = item.candidate.identifiers.canonical_key(item.candidate.title)
        if key not in seen:
            selected.append(item)
            seen.add(key)
        if len(selected) >= max_selected:
            break
    return selected


def _bucket(item: RankedCandidate) -> str:
    provenance = item.candidate.query_provenance
    return provenance.target_section or provenance.intent or item.candidate.provider_name
