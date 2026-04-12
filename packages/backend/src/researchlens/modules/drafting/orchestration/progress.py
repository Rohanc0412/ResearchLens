from typing import Protocol

from researchlens.modules.drafting.application.ports import DraftingProgressSink


class DraftingGraphEventSink(Protocol):
    async def info(self, *, key: str, message: str, payload: dict[str, object]) -> None: ...

    async def warning(self, *, key: str, message: str, payload: dict[str, object]) -> None: ...


class DraftingGraphCheckpointSink(Protocol):
    async def checkpoint(
        self,
        *,
        key: str,
        summary: dict[str, object],
        completed_stages: tuple[str, ...],
        next_stage: str | None,
    ) -> None: ...


class DraftingGraphProgressWriter(DraftingProgressSink):
    def __init__(self, events: DraftingGraphEventSink) -> None:
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
