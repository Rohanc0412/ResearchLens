import asyncio
from dataclasses import asdict
from typing import Protocol
from uuid import UUID

from researchlens.modules.drafting.application import RunDraftingStageUseCase
from researchlens.modules.drafting.application.ports import (
    DraftingProgressSink,
    DraftingRepository,
    DraftingRunInputReader,
    RunCancellationProbe,
)
from researchlens.shared.config import ResearchLensSettings
from researchlens.shared.llm.factory import build_llm_client
from researchlens.shared.llm.ports import StructuredGenerationClient


class DraftingStageEventWriter(Protocol):
    async def info(self, *, key: str, message: str, payload: dict[str, object]) -> None: ...

    async def warning(self, *, key: str, message: str, payload: dict[str, object]) -> None: ...


class DraftingStageCheckpointWriter(Protocol):
    async def checkpoint(self, *, key: str, summary: dict[str, object]) -> None: ...


class DraftingStageOrchestrator:
    def __init__(
        self,
        *,
        settings: ResearchLensSettings,
        input_reader: DraftingRunInputReader,
        cancellation_probe: RunCancellationProbe,
        repository: DraftingRepository,
        generation_client: StructuredGenerationClient | None = None,
    ) -> None:
        if settings.llm.provider == "disabled" or not settings.llm.api_key:
            raise ValueError("Drafting requires an enabled real LLM provider.")
        self._repository = repository
        self._timeout_seconds = settings.drafting.stage_timeout_seconds
        self._use_case = RunDraftingStageUseCase(
            settings=settings.drafting,
            input_reader=input_reader,
            repository=repository,
            generation_client=generation_client or build_llm_client(settings.llm),
            cancellation_probe=cancellation_probe,
            provider_name=settings.llm.provider,
        )

    async def execute(
        self,
        *,
        run_id: UUID,
        events: DraftingStageEventWriter,
        checkpoints: DraftingStageCheckpointWriter,
    ) -> None:
        await events.info(key="draft.preparing", message="Draft preparation started", payload={})
        try:
            async with asyncio.timeout(self._timeout_seconds):
                result = await self._use_case.execute(
                    run_id=run_id,
                    progress=_DraftingProgressEventWriter(events),
                )
        except Exception as exc:
            await events.warning(
                key="draft.failed",
                message="Draft stage failed",
                payload={"reason": str(exc)},
            )
            raise
        summary = asdict(result)
        await checkpoints.checkpoint(key="draft:assembled", summary=summary)
        await events.info(
            key="draft.report_assembled",
            message="Draft report assembled",
            payload=summary,
        )


class _DraftingProgressEventWriter(DraftingProgressSink):
    def __init__(self, events: DraftingStageEventWriter) -> None:
        self._events = events

    async def evidence_pack_ready(self, *, section_id: str, evidence_count: int) -> None:
        await self._events.info(
            key=f"draft.evidence_pack_ready:{section_id}",
            message="Draft evidence pack ready",
            payload={"section_id": section_id, "evidence_count": evidence_count},
        )

    async def section_started(self, *, section_id: str) -> None:
        await self._events.info(
            key=f"draft.section_started:{section_id}",
            message="Draft section started",
            payload={"section_id": section_id},
        )

    async def section_completed(self, *, section_id: str) -> None:
        await self._events.info(
            key=f"draft.section_completed:{section_id}",
            message="Draft section completed",
            payload={"section_id": section_id},
        )

    async def correction_retry(self, *, section_id: str, reason: str, attempt: int) -> None:
        await self._events.warning(
            key=f"draft.correction_retry:{section_id}:{attempt}",
            message="Draft section correction retry",
            payload={"section_id": section_id, "attempt": attempt, "reason": reason},
        )
