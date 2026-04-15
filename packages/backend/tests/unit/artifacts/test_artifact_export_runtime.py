from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

import pytest

from researchlens.modules.artifacts.application import ExportReportResult
from researchlens.modules.artifacts.orchestration.graph_runtime import ArtifactExportGraphRuntime


class _FakeExportReport:
    def __init__(self) -> None:
        self.executed_inside_boundary = False

    async def execute(self, *, run_id: UUID) -> ExportReportResult:
        self.executed_inside_boundary = _FakeTransactionManager.inside_boundary
        return ExportReportResult(
            artifact_ids=(uuid4(), uuid4()),
            artifact_count=2,
            warning_count=0,
        )


class _FakeTransactionManager:
    inside_boundary = False

    def __init__(self) -> None:
        self.boundaries = 0

    @asynccontextmanager
    async def boundary(self) -> AsyncIterator[None]:
        self.boundaries += 1
        _FakeTransactionManager.inside_boundary = True
        try:
            yield
        finally:
            _FakeTransactionManager.inside_boundary = False


class _FakeEvents:
    def __init__(self) -> None:
        self.keys: list[str] = []

    async def info(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        self.keys.append(key)

    async def warning(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        self.keys.append(key)


class _FakeCheckpoints:
    def __init__(self) -> None:
        self.summary: dict[str, object] | None = None

    async def checkpoint(
        self,
        *,
        key: str,
        summary: dict[str, object],
        completed_stages: tuple[str, ...],
        next_stage: str | None,
    ) -> None:
        self.summary = summary


@pytest.mark.asyncio
async def test_export_runtime_persists_artifacts_inside_transaction_boundary() -> None:
    export_report = _FakeExportReport()
    transaction_manager = _FakeTransactionManager()
    events = _FakeEvents()
    checkpoints = _FakeCheckpoints()
    runtime = ArtifactExportGraphRuntime(
        export_report=export_report,  # type: ignore[arg-type]
        transaction_manager=transaction_manager,
        events=events,
        checkpoints=checkpoints,
    )

    result = await runtime.export(run_id=uuid4(), completed_stages=("retrieve", "draft"))

    assert result.artifact_count == 2
    assert transaction_manager.boundaries == 1
    assert export_report.executed_inside_boundary is True
    assert events.keys == ["export.started", "export.completed"]
    assert checkpoints.summary is not None
    assert checkpoints.summary["artifact_count"] == 2
