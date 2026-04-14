import asyncio
from typing import Protocol

from researchlens.modules.repair.application import RepairProgressSink, SectionRepairOutcome


class RepairGraphEventSink(Protocol):
    async def info(self, *, key: str, message: str, payload: dict[str, object]) -> None: ...

    async def warning(self, *, key: str, message: str, payload: dict[str, object]) -> None: ...


class RepairGraphCheckpointSink:
    async def checkpoint(
        self,
        *,
        key: str,
        summary: dict[str, object],
        completed_stages: tuple[str, ...],
        next_stage: str | None,
    ) -> None:
        return None


class RepairGraphProgressWriter(RepairProgressSink):
    def __init__(self, events: RepairGraphEventSink) -> None:
        self._events = events
        self._lock = asyncio.Lock()

    async def selected(self, *, section_id: str) -> None:
        async with self._lock:
            await self._events.info(
                key=f"repair.section_selected.{section_id}",
                message=f"Selected section {section_id} for repair",
                payload={"section_id": section_id},
            )

    async def started(self, *, section_id: str) -> None:
        async with self._lock:
            await self._events.info(
                key=f"repair.section_started.{section_id}",
                message=f"Repairing section {section_id}",
                payload={"section_id": section_id},
            )

    async def completed(self, *, outcome: SectionRepairOutcome) -> None:
        key = (
            "repair.section_fallback_applied"
            if outcome.action == "fallback_edit"
            else "repair.section_completed"
        )
        async with self._lock:
            await self._events.info(
                key=f"{key}.{outcome.section_id}",
                message=f"Repair section {outcome.section_id} finished with {outcome.action}",
                payload=outcome.model_dump(mode="json"),
            )
