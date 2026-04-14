import asyncio

import pytest

from researchlens.modules.drafting.orchestration.progress import DraftingGraphProgressWriter


class _RecordingEventSink:
    def __init__(self) -> None:
        self.active_calls = 0
        self.max_active_calls = 0
        self.calls: list[tuple[str, str]] = []

    async def info(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        self.active_calls += 1
        self.max_active_calls = max(self.max_active_calls, self.active_calls)
        await asyncio.sleep(0)
        self.calls.append((key, message))
        self.active_calls -= 1

    async def warning(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        await self.info(key=key, message=message, payload=payload)


@pytest.mark.asyncio
async def test_drafting_progress_writer_serializes_concurrent_events() -> None:
    sink = _RecordingEventSink()
    writer = DraftingGraphProgressWriter(sink)

    await asyncio.gather(
        writer.evidence_pack_ready(section_id="overview", evidence_count=2),
        writer.section_started(section_id="overview"),
        writer.section_completed(section_id="overview"),
    )

    assert sink.max_active_calls == 1
    assert len(sink.calls) == 3
