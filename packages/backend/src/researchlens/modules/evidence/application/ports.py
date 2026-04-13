from typing import Protocol
from uuid import UUID

from researchlens.modules.evidence.application.dtos import (
    ChunkDetail,
    RunEvidenceSummary,
    SectionEvidenceTrace,
    SourceDetail,
)


class EvidenceQueries(Protocol):
    async def run_summary(self, *, tenant_id: UUID, run_id: UUID) -> RunEvidenceSummary | None: ...

    async def section_trace(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
        section_id: str,
    ) -> SectionEvidenceTrace | None: ...

    async def chunk_detail(
        self,
        *,
        tenant_id: UUID,
        chunk_id: UUID,
        context_window: int,
    ) -> ChunkDetail | None: ...

    async def source_detail(self, *, tenant_id: UUID, source_id: UUID) -> SourceDetail | None: ...
