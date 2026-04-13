from researchlens.modules.artifacts.application.citation_resolution import replace_citation_tokens
from researchlens.modules.artifacts.domain.artifact_kind import ArtifactKind
from researchlens.modules.artifacts.domain.export_models import RenderedArtifact, ReportExportBundle


def render_report_markdown(bundle: ReportExportBundle) -> RenderedArtifact:
    lines = [f"# {bundle.report_title}", ""]
    for section in bundle.sections:
        lines.extend(
            [
                f"## {section.title}",
                "",
                replace_citation_tokens(section.text, bundle.citations),
                "",
            ]
        )
    if bundle.citations:
        lines.extend(["## References", ""])
        source_by_id = {source.source_id: source for source in bundle.sources}
        for citation in bundle.citations:
            source = source_by_id[citation.source_id]
            title = source.title or source.canonical_key
            lines.append(f"[{citation.citation_label}] {title} (chunk {citation.chunk_id})")
    content = "\n".join(lines).strip() + "\n"
    return RenderedArtifact(
        kind=ArtifactKind.FINAL_REPORT_MARKDOWN.value,
        filename=f"run-{bundle.run_id}-final-report.md",
        media_type="text/markdown; charset=utf-8",
        content=content.encode("utf-8"),
        metadata={"report_title": bundle.report_title},
    )
