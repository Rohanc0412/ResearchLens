import asyncio
from datetime import UTC, datetime
from typing import Protocol

from researchlens.modules.runs.domain import Run, RunStage


class RunClock(Protocol):
    def now(self) -> datetime: ...


class UtcRunClock:
    def now(self) -> datetime:
        return datetime.now(tz=UTC)


class SleepStageExecutionController:
    def __init__(self, delay_ms: int) -> None:
        self._delay_ms = delay_ms

    async def before_stage(self, *, run: Run, stage: RunStage) -> None:
        if self._delay_ms > 0:
            await asyncio.sleep(self._delay_ms / 1000)

    async def after_stage(self, *, run: Run, stage: RunStage) -> None:
        return None
