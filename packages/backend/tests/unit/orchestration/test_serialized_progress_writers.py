import asyncio
from uuid import uuid4

import pytest

from researchlens.modules.evaluation.orchestration.progress import EvaluationGraphProgressWriter
from researchlens.modules.repair.application import SectionRepairOutcome
from researchlens.modules.repair.orchestration.progress import RepairGraphProgressWriter


class _RecordingEventSink:
    def __init__(self) -> None:
        self.active_calls = 0
        self.max_active_calls = 0
        self.calls = 0

    async def info(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        self.active_calls += 1
        self.max_active_calls = max(self.max_active_calls, self.active_calls)
        await asyncio.sleep(0)
        self.calls += 1
        self.active_calls -= 1

    async def warning(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        await self.info(key=key, message=message, payload=payload)


@pytest.mark.asyncio
async def test_evaluation_progress_writer_serializes_concurrent_events() -> None:
    sink = _RecordingEventSink()
    writer = EvaluationGraphProgressWriter(sink)

    await asyncio.gather(
        writer.section_started(section_title="Overview"),
        writer.section_completed(section_title="Overview"),
    )

    assert sink.max_active_calls == 1
    assert sink.calls == 2


@pytest.mark.asyncio
async def test_repair_progress_writer_serializes_concurrent_events() -> None:
    sink = _RecordingEventSink()
    writer = RepairGraphProgressWriter(sink)
    outcome = SectionRepairOutcome(
        repair_result_id=uuid4(),
        section_id="overview",
        action="updated",
        status="completed",
        changed=True,
        revised_text="Text [[chunk:11111111-1111-1111-1111-111111111111]]",
        revised_summary="Bridge",
    )

    await asyncio.gather(
        writer.selected(section_id="overview"),
        writer.started(section_id="overview"),
        writer.completed(outcome=outcome),
    )

    assert sink.max_active_calls == 1
    assert sink.calls == 3
