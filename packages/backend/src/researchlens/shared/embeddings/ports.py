from typing import Protocol

from researchlens.shared.embeddings.domain import EmbeddingRequest, EmbeddingResult


class EmbeddingClient(Protocol):
    @property
    def model(self) -> str: ...

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult: ...
