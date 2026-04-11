import asyncio

import pytest

from researchlens.modules.retrieval.infrastructure.ingestion.content_selection import (
    choose_ingestible_content,
)
from researchlens.shared.embeddings.batching import (
    EmbeddingBatch,
    embed_batches_bounded,
    split_embedding_batches,
)


def test_content_selection_prefers_full_text_then_abstract_then_title() -> None:
    assert choose_ingestible_content(title="T", abstract="A", full_text="F").text == "F"
    assert choose_ingestible_content(title="T", abstract="A", full_text=None).text == "A"
    assert choose_ingestible_content(title="T", abstract=None, full_text=None).text == "T"


def test_embedding_batches_respect_batch_size() -> None:
    batches = split_embedding_batches(["a", "b", "c"], batch_size=2)

    assert batches == [
        EmbeddingBatch(index=0, texts=("a", "b")),
        EmbeddingBatch(index=1, texts=("c",)),
    ]


@pytest.mark.asyncio
async def test_embed_batches_bounded_respects_concurrency() -> None:
    active = 0
    max_active = 0

    async def embed(texts: tuple[str, ...]) -> list[list[float]]:
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        active -= 1
        return [[float(len(text))] for text in texts]

    result = await embed_batches_bounded(
        batches=split_embedding_batches(["a", "bb", "ccc", "dddd"], batch_size=1),
        max_concurrent_batches=2,
        embed_batch=embed,
    )

    assert result == [[1.0], [2.0], [3.0], [4.0]]
    assert max_active == 2
