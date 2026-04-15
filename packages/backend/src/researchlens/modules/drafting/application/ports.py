from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Protocol
from uuid import UUID

from researchlens.modules.drafting.application.dto import RunDraftingInput
from researchlens.modules.drafting.domain import ReportDraft, SectionBrief, SectionDraft
from researchlens.shared.llm.domain import StructuredGenerationRequest, StructuredGenerationResult


class DraftingRunInputReader(Protocol):
    async def load_run_drafting_input(self, *, run_id: UUID) -> RunDraftingInput: ...


class DraftingRepository(Protocol):

    async def replace_section_preparation(
        self,
        *,
        run_id: UUID,
        briefs: tuple[SectionBrief, ...],
    ) -> None: ...

    async def replace_section_draft(self, *, draft: SectionDraft) -> None: ...

    async def list_persisted_section_drafts(self, *, run_id: UUID) -> tuple[SectionDraft, ...]: ...

    async def replace_report_draft(self, *, draft: ReportDraft) -> None: ...


class TransactionManager(Protocol):
    @asynccontextmanager
    async def boundary(self) -> AsyncIterator[None]:
        yield


class DraftingGenerationClient(Protocol):
    @property
    def model(self) -> str: ...

    async def generate_structured(
        self,
        request: StructuredGenerationRequest,
    ) -> StructuredGenerationResult: ...


class RunCancellationProbe(Protocol):
    async def cancel_requested(self, *, run_id: UUID) -> bool: ...


class DraftingProgressSink(Protocol):
    async def evidence_pack_ready(self, *, section_id: str, evidence_count: int) -> None: ...

    async def section_started(self, *, section_id: str) -> None: ...

    async def section_completed(self, *, section_id: str) -> None: ...

    async def correction_retry(self, *, section_id: str, reason: str, attempt: int) -> None: ...
