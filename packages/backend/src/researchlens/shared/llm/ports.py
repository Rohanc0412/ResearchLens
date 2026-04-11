from typing import Protocol

from researchlens.shared.llm.domain import StructuredGenerationRequest, StructuredGenerationResult


class StructuredGenerationClient(Protocol):
    @property
    def model(self) -> str: ...

    async def generate_structured(
        self,
        request: StructuredGenerationRequest,
    ) -> StructuredGenerationResult: ...
