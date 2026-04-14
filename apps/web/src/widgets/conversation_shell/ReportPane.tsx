import { Link } from "react-router-dom";

import {
  useEvaluationIssuesQuery,
  useEvaluationSummaryQuery,
  useRunEvidenceSummaryQuery,
} from "../../entities/evidence/evidence.api";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";

export function ReportPane({ runId }: { runId?: string | null }) {
  const evidence = useRunEvidenceSummaryQuery(runId ?? "");
  const evaluation = useEvaluationSummaryQuery(runId ?? "");
  const issues = useEvaluationIssuesQuery(runId ?? "");

  if (!runId) {
    return (
      <Card className="workspace-panel" title="Report surface" meta="Waiting for a run">
        Start research from the composer to populate artifacts, evidence traces, and evaluation signals.
      </Card>
    );
  }

  return (
    <Card
      className="workspace-panel"
      title="Report surface"
      meta="Evidence, evaluation, artifacts"
      actions={
        <Link to={`/runs/${runId}/artifacts`}>
          <Button compact variant="primary">
            Open review
          </Button>
        </Link>
      }
    >
      <div className="workspace-report">
        {evidence.error || evaluation.error ? (
          <ErrorBanner body="Report support data could not be loaded." />
        ) : null}
        <div className="metric-grid">
          <div>
            <span className="metric-grid__value">{evidence.data?.section_count ?? "-"}</span>
            <span className="meta-line">sections</span>
          </div>
          <div>
            <span className="metric-grid__value">{evidence.data?.chunk_count ?? "-"}</span>
            <span className="meta-line">snippets</span>
          </div>
          <div>
            <span className="metric-grid__value">
              {evaluation.data ? `${evaluation.data.quality_pct.toFixed(0)}%` : "-"}
            </span>
            <span className="meta-line">quality</span>
          </div>
        </div>
        <div className="section-list">
          {(evidence.data?.sections ?? []).slice(0, 6).map((section) => (
            <Link
              key={section.section_id}
              className="section-row"
              to={`/runs/${runId}/artifacts?section=${section.section_id}`}
            >
              <div>
                <strong>{section.title}</strong>
                <div className="meta-line">
                  {section.issue_count} issues | {section.repaired ? "repaired" : "canonical"}
                </div>
              </div>
              <span className="pill">Inspect</span>
            </Link>
          ))}
          {(evidence.data?.sections.length ?? 0) === 0 ? (
            <div className="meta-line">Evidence sections will appear here as the run completes.</div>
          ) : null}
        </div>
        {(issues.data ?? []).length > 0 ? (
          <div className="event-log">
            {(issues.data ?? []).slice(0, 3).map((issue) => (
              <div key={issue.issue_id} className="event-log__item">
                <strong>{issue.message}</strong>
                <div className="meta-line">
                  {issue.section_title} | {issue.severity}
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </Card>
  );
}
