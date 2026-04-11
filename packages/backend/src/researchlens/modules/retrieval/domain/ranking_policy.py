from dataclasses import dataclass
from math import log10

from researchlens.modules.retrieval.domain.candidate import NormalizedSearchCandidate
from researchlens.modules.retrieval.domain.query_plan import RetrievalQuery


@dataclass(frozen=True, slots=True)
class RankingWeights:
    lexical: float
    embedding: float
    recency: float
    citation: float


@dataclass(frozen=True, slots=True)
class ScoreBreakdown:
    lexical: float
    embedding: float
    recency: float
    citation: float
    total: float


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    candidate: NormalizedSearchCandidate
    score_breakdown: ScoreBreakdown


def rank_candidates(
    *,
    candidates: list[NormalizedSearchCandidate],
    queries: list[RetrievalQuery],
    weights: RankingWeights,
    embedding_scores: dict[str, float],
    current_year: int = 2026,
) -> list[RankedCandidate]:
    ranked = []
    query_terms = _terms(" ".join(query.query for query in queries))
    for candidate in candidates:
        key = candidate.identifiers.canonical_key(candidate.title)
        lexical = _lexical(candidate, query_terms)
        embedding = embedding_scores.get(key, 0.0)
        recency = _recency(candidate.year, current_year)
        citation = _citation(candidate.citation_count)
        total = (
            weights.lexical * lexical
            + weights.embedding * embedding
            + weights.recency * recency
            + weights.citation * citation
        )
        ranked.append(
            RankedCandidate(
                candidate=candidate,
                score_breakdown=ScoreBreakdown(lexical, embedding, recency, citation, total),
            )
        )
    return sorted(
        ranked,
        key=lambda item: (
            -item.score_breakdown.total,
            item.candidate.title or "",
            item.candidate.provider_name,
        ),
    )


def _lexical(candidate: NormalizedSearchCandidate, query_terms: set[str]) -> float:
    if not query_terms:
        return 0.0
    candidate_terms = _terms(" ".join([candidate.title or "", candidate.abstract or ""]))
    return len(candidate_terms & query_terms) / len(query_terms)


def _terms(value: str) -> set[str]:
    return {term for term in value.casefold().replace("-", " ").split() if len(term) > 2}


def _recency(year: int | None, current_year: int) -> float:
    if year is None or year > current_year:
        return 0.0
    return max(0.0, 1.0 - ((current_year - year) / 20.0))


def _citation(value: int | None) -> float:
    if not value or value < 1:
        return 0.0
    return min(1.0, log10(value + 1) / 3.0)
