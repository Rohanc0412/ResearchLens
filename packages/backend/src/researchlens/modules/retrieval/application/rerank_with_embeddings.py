from math import sqrt

from researchlens.modules.retrieval.domain.ranking_policy import RankedCandidate
from researchlens.shared.embeddings.batching import (
    embed_batches_bounded,
    split_embedding_batches,
)
from researchlens.shared.embeddings.domain import EmbeddingRequest
from researchlens.shared.embeddings.ports import EmbeddingClient


class EmbeddingReranker:
    def __init__(
        self,
        *,
        client: EmbeddingClient,
        batch_size: int,
        max_concurrent_batches: int,
    ) -> None:
        self._client = client
        self._batch_size = batch_size
        self._max_concurrent_batches = max_concurrent_batches

    async def score_top_k(
        self,
        ranked: list[RankedCandidate],
        *,
        top_k: int,
        query_text: str,
    ) -> dict[str, float]:
        top = ranked[:top_k]
        texts = [query_text, *[_candidate_text(item) for item in top]]
        batches = split_embedding_batches(texts, batch_size=self._batch_size)
        vectors = await embed_batches_bounded(
            batches=batches,
            max_concurrent_batches=self._max_concurrent_batches,
            embed_batch=self._embed_texts,
        )
        if not vectors:
            return {}
        query_vector = vectors[0]
        scores: dict[str, float] = {}
        for item, vector in zip(top, vectors[1:], strict=False):
            key = item.candidate.identifiers.canonical_key(item.candidate.title)
            scores[key] = _cosine(query_vector, vector)
        return scores

    async def _embed_texts(self, texts: tuple[str, ...]) -> list[list[float]]:
        result = await self._client.embed(EmbeddingRequest(texts=texts))
        return [list(vector) for vector in result.vectors]


def _candidate_text(item: RankedCandidate) -> str:
    return "\n".join(
        value for value in [item.candidate.title, item.candidate.abstract] if value
    )


def _cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(
        left_value * right_value
        for left_value, right_value in zip(left, right, strict=False)
    )
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
