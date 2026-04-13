from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.artifacts.application.citation_resolution import resolve_citations
from researchlens.modules.artifacts.application.persist_export_artifacts import (
    PersistExportArtifactsUseCase,
)
from researchlens.modules.artifacts.application.ports import ExportBundleReader
from researchlens.modules.artifacts.domain.export_models import ReportExportBundle


@dataclass(frozen=True, slots=True)
class ExportReportResult:
    artifact_ids: tuple[UUID, ...]
    artifact_count: int
    warning_count: int


class ExportReportUseCase:
    def __init__(
        self,
        *,
        bundle_reader: ExportBundleReader,
        persist_artifacts: PersistExportArtifactsUseCase,
    ) -> None:
        self._bundle_reader = bundle_reader
        self._persist_artifacts = persist_artifacts

    async def execute(self, *, run_id: UUID) -> ExportReportResult:
        bundle = await self._bundle_reader.load_bundle(run_id=run_id)
        bundle = _with_resolved_citations(bundle)
        artifacts = await self._persist_artifacts.execute(bundle=bundle)
        return ExportReportResult(
            artifact_ids=tuple(item.id for item in artifacts),
            artifact_count=len(artifacts),
            warning_count=len(bundle.warnings),
        )


def _with_resolved_citations(bundle: ReportExportBundle) -> ReportExportBundle:
    citations = resolve_citations(
        section_texts=tuple(section.text for section in bundle.sections),
        chunks=bundle.chunks,
    )
    return bundle.__class__(
        tenant_id=bundle.tenant_id,
        project_id=bundle.project_id,
        run_id=bundle.run_id,
        conversation_id=bundle.conversation_id,
        report_title=bundle.report_title,
        sections=bundle.sections,
        chunks=bundle.chunks,
        sources=bundle.sources,
        citations=citations,
        latest_evaluation_pass_id=bundle.latest_evaluation_pass_id,
        latest_repair_pass_id=bundle.latest_repair_pass_id,
        warnings=bundle.warnings,
    )
