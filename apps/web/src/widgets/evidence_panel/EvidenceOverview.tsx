import { Link } from "react-router-dom";

import {
  useRunEvidenceSummaryQuery,
  useSectionEvidenceQuery,
} from "../../entities/evidence/evidence.api";
import { Card } from "../../shared/ui/Card";
import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";

export function EvidenceOverview({
  runId,
  sectionId,
}: {
  runId: string;
  sectionId?: string | null;
}) {
  const summary = useRunEvidenceSummaryQuery(runId);
  const section = useSectionEvidenceQuery(runId, sectionId ?? "");

  if (summary.error) {
    return <ErrorBanner body="Evidence summary could not be loaded." />;
  }

  if (!summary.isLoading && !summary.data) {
    return (
      <EmptyState
        title="No evidence available"
        body="This run does not expose persisted evidence yet."
      />
    );
  }

  return (
    <div className="evidence-workbench">
      <Card className="workspace-panel" title="Sections" meta={summary.data ? `${summary.data.section_count} sections` : "Loading"}>
        <div className="stack">
          {(summary.data?.sections ?? []).map((item) => (
            <div key={item.section_id} className="section-row">
              <div>
                <strong>{item.title}</strong>
                <div className="meta-line">
                  {item.issue_count} issues | {item.repaired ? "Repaired" : "Draft canonical"}
                </div>
              </div>
              <Link to={`/runs/${runId}/artifacts?section=${item.section_id}`}>
                <span className="pill">Inspect</span>
              </Link>
            </div>
          ))}
        </div>
      </Card>
      <Card className="preview-panel" title="Section trace" meta={sectionId ?? "Choose a section"}>
        {section.error ? <ErrorBanner body="Section trace could not be loaded." /> : null}
        {section.data ? (
          <div className="stack">
            <p className="page-subtitle">{section.data.canonical_summary}</p>
            {(section.data.evidence_chunks ?? []).map((chunk) => (
              <div key={chunk.chunk_id} className="evidence-chunk">
                <div className="stack">
                  <strong>{chunk.source_title ?? "Untitled source"}</strong>
                  <div>{chunk.excerpt_text}</div>
                  <Link to={`/evidence/snippets/${chunk.chunk_id}`}>
                    <span className="pill">Open snippet</span>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : section.isLoading && sectionId ? (
          <div className="meta-line">Loading section trace...</div>
        ) : sectionId ? (
          <div className="meta-line">Section trace is not available for this run yet.</div>
        ) : (
          <div className="meta-line">Choose a section to inspect claim and source traces.</div>
        )}
      </Card>
    </div>
  );
}
