import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  useArtifactDownloadMutation,
  useArtifactsQuery,
} from "../../entities/artifact/artifact.api";
import {
  useEvaluationIssuesQuery,
  useEvaluationSummaryQuery,
  useRepairSummaryQuery,
  useRunEvidenceSummaryQuery,
} from "../../entities/evidence/evidence.api";
import { formatDateTime } from "../../shared/lib/format";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";

export function ArtifactBrowser({ runId }: { runId: string }) {
  const artifacts = useArtifactsQuery(runId);
  const evidence = useRunEvidenceSummaryQuery(runId);
  const evaluation = useEvaluationSummaryQuery(runId);
  const issues = useEvaluationIssuesQuery(runId);
  const repair = useRepairSummaryQuery(runId);
  const download = useArtifactDownloadMutation();
  const [previewText, setPreviewText] = useState("");
  const [previewTitle, setPreviewTitle] = useState("");

  useEffect(() => {
    if (!download.data) {
      return;
    }

    if (download.data.mediaType.includes("json") || download.data.mediaType.startsWith("text/")) {
      void download.data.blob.text().then(setPreviewText);
    }
  }, [download.data]);

  if (artifacts.error) {
    return <ErrorBanner body="Artifacts could not be loaded." />;
  }

  if (!artifacts.isLoading && (artifacts.data?.length ?? 0) === 0) {
    return (
      <EmptyState
        title="No artifacts yet"
        body="This run has not produced exportable artifacts."
      />
    );
  }

  return (
    <div className="grid grid--2">
      <div className="stack">
        <Card title="Artifacts" meta={`Run ${runId}`}>
          <div className="artifact-list">
            {(artifacts.data ?? []).map((artifact) => (
              <Card
                key={artifact.id}
                title={artifact.filename}
                meta={`${artifact.kind} • ${artifact.media_type} • ${formatDateTime(
                  artifact.created_at,
                )}`}
              >
                <div className="row row--between">
                  <div className="meta-line">{artifact.byte_size} bytes</div>
                  <div className="row">
                    <Button
                      compact
                      onClick={() =>
                        void download.mutateAsync(artifact).then(({ blob, filename, mediaType }) => {
                          setPreviewTitle(filename);
                          const link = document.createElement("a");
                          link.href = URL.createObjectURL(blob);
                          link.download = filename;
                          link.click();
                          URL.revokeObjectURL(link.href);
                          if (mediaType.startsWith("text/") || mediaType.includes("json")) {
                            void blob.text().then(setPreviewText);
                          }
                        })
                      }
                    >
                      Download
                    </Button>
                    <Link to={`/runs/${runId}/artifacts#evidence`}>
                      <Button compact variant="ghost">
                        Evidence
                      </Button>
                    </Link>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </Card>

        <Card title="Evidence linkage" meta="Read-only evidence state">
          {evidence.data ? (
            <div className="stack">
              <div className="meta-line">
                {evidence.data.section_count} sections • {evidence.data.chunk_count} snippets •{" "}
                {evidence.data.source_count} sources
              </div>
              {(evidence.data.sections ?? []).map((section) => (
                <div key={section.section_id} className="row row--between">
                  <strong>{section.title}</strong>
                  <Link to={`/runs/${runId}/artifacts?section=${section.section_id}`}>
                    <span className="pill">Open section</span>
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <div className="meta-line">Loading evidence summary...</div>
          )}
        </Card>
      </div>

      <div className="stack">
        <Card title="Preview" meta={previewTitle || "Download a text artifact to preview it"}>
          <div className="preview">
            <pre>{previewText || "Preview appears here for markdown, text, and manifest artifacts."}</pre>
          </div>
        </Card>

        <Card title="Evaluation" meta="Current backend summary">
          {evaluation.data ? (
            <div className="stack">
              <div className="row row--between">
                <span className="pill">{evaluation.data.quality_pct.toFixed(1)}% quality</span>
                <span className="meta-line">
                  {evaluation.data.issue_count} issues • {evaluation.data.sections_requiring_repair_count} repair
                </span>
              </div>
              {(issues.data ?? []).slice(0, 5).map((issue) => (
                <div key={issue.issue_id} className="card">
                  <div className="card__body">
                    <strong>{issue.message}</strong>
                    <div className="meta-line">
                      {issue.section_title} • {issue.severity}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="meta-line">No evaluation summary available.</div>
          )}
        </Card>

        <Card title="Repair" meta="If a repair result exists, it appears here">
          <div className="meta-line">
            {repair.data
              ? `${repair.data.changed_count} sections changed`
              : "No repair summary available for this run."}
          </div>
        </Card>
      </div>
    </div>
  );
}
