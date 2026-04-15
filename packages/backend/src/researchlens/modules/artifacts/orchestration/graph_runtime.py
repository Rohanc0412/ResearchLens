from uuid import UUID

from researchlens.modules.artifacts.application import ExportReportResult, ExportReportUseCase
from researchlens.modules.artifacts.application.ports import TransactionManager
from researchlens.modules.artifacts.orchestration.progress import (
    ArtifactExportCheckpointSink,
    ArtifactExportEventSink,
)


class ArtifactExportGraphRuntime:
    def __init__(
        self,
        *,
        export_report: ExportReportUseCase,
        transaction_manager: TransactionManager,
        events: ArtifactExportEventSink,
        checkpoints: ArtifactExportCheckpointSink,
    ) -> None:
        self._export_report = export_report
        self._transaction_manager = transaction_manager
        self._events = events
        self._checkpoints = checkpoints

    async def export(
        self,
        *,
        run_id: UUID,
        completed_stages: tuple[str, ...],
    ) -> ExportReportResult:
        await self._events.info(key="export.started", message="Artifact export started", payload={})
        async with self._transaction_manager.boundary():
            result = await self._export_report.execute(run_id=run_id)
        summary = {
            "artifact_ids": [str(item) for item in result.artifact_ids],
            "artifact_count": result.artifact_count,
            "warning_count": result.warning_count,
        }
        await self._checkpoints.checkpoint(
            key="export:completed",
            summary=summary,
            completed_stages=completed_stages,
            next_stage=None,
        )
        await self._events.info(
            key="export.completed",
            message="Artifact export completed",
            payload=summary,
        )
        return result
