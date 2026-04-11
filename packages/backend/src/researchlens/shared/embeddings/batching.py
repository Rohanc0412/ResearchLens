import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EmbeddingBatch:
    index: int
    texts: tuple[str, ...]


def split_embedding_batches(texts: list[str], *, batch_size: int) -> list[EmbeddingBatch]:
    if batch_size <= 0:
        raise ValueError("Embedding batch size must be positive.")
    return [
        EmbeddingBatch(index=index, texts=tuple(texts[start : start + batch_size]))
        for index, start in enumerate(range(0, len(texts), batch_size))
    ]


async def embed_batches_bounded(
    *,
    batches: list[EmbeddingBatch],
    max_concurrent_batches: int,
    embed_batch: Callable[[tuple[str, ...]], Awaitable[list[list[float]]]],
) -> list[list[float]]:
    limiter = asyncio.Semaphore(max_concurrent_batches)

    async def run_batch(batch: EmbeddingBatch) -> tuple[int, list[list[float]]]:
        async with limiter:
            return batch.index, await embed_batch(batch.texts)

    results = await asyncio.gather(*(run_batch(batch) for batch in batches))
    ordered = sorted(results, key=lambda item: item[0])
    return [vector for _, vectors in ordered for vector in vectors]
