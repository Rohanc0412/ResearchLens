from researchlens.modules.artifacts.domain.export_models import ReportExportBundle


def build_manifest_json(bundle: ReportExportBundle) -> dict[str, object]:
    return {
        "run_id": str(bundle.run_id),
        "project_id": str(bundle.project_id),
        "conversation_id": str(bundle.conversation_id) if bundle.conversation_id else None,
        "report_title": bundle.report_title,
        "sections": [
            {
                "section_id": section.section_id,
                "title": section.title,
                "order": section.section_order,
                "draft_id": str(section.draft_id),
                "repaired": section.repaired,
                "repair_result_id": (
                    str(section.repair_result_id) if section.repair_result_id else None
                ),
            }
            for section in bundle.sections
        ],
        "citation_map": [
            {
                "label": item.citation_label,
                "chunk_id": str(item.chunk_id),
                "source_id": str(item.source_id),
            }
            for item in bundle.citations
        ],
        "chunks": [
            {
                "chunk_id": str(chunk.chunk_id),
                "source_id": str(chunk.source_id),
                "chunk_index": chunk.chunk_index,
            }
            for chunk in bundle.chunks
        ],
        "sources": [
            {
                "source_id": str(source.source_id),
                "canonical_key": source.canonical_key,
                "title": source.title,
                "identifiers": source.identifiers,
                "metadata": source.metadata,
            }
            for source in bundle.sources
        ],
        "latest_evaluation_pass_id": (
            str(bundle.latest_evaluation_pass_id) if bundle.latest_evaluation_pass_id else None
        ),
        "latest_repair_pass_id": str(bundle.latest_repair_pass_id)
        if bundle.latest_repair_pass_id
        else None,
        "warnings": list(bundle.warnings),
    }
