import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import { Link } from "react-router-dom";
import remarkGfm from "remark-gfm";

import {
  useArtifactDownloadMutation,
  useArtifactsQuery,
  useArtifactTextQuery,
} from "../../entities/artifact/artifact.api";
import { useRunQuery } from "../../entities/run/run.api";
import { Button } from "../../shared/ui/Button";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { RunProgressCard } from "../run_progress/RunProgressCard";
import {
  extractReportTitle,
  normalizeReportMarkdown,
  reportMarkdownComponents,
  stripReportTitle,
} from "./reportMarkdown";

function downloadBlob(blob: Blob, filename: string) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

function reportStatusClass(status: string | undefined) {
  if (status === "succeeded") return "pill pill--success";
  if (status === "failed" || status === "canceled") return "pill pill--danger";
  return "pill pill--warning";
}

export function ReportPane({
  runId,
  conversationTitle,
}: {
  runId?: string | null;
  conversationTitle?: string;
}) {
  const run = useRunQuery(runId ?? "");
  const artifacts = useArtifactsQuery(runId ?? "", {
    enabled: Boolean(runId),
    refetchInterval:
      run.data && ["succeeded", "failed", "canceled"].includes(run.data.status) ? false : 2500,
  });
  const download = useArtifactDownloadMutation();

  const reportArtifact = useMemo(
    () =>
      (artifacts.data ?? []).find(
        (artifact) =>
          artifact.kind === "report_markdown" ||
          artifact.media_type === "text/markdown",
      ) ?? null,
    [artifacts.data],
  );
  const report = useArtifactTextQuery(reportArtifact?.id ?? "", reportArtifact?.filename, {
    enabled: Boolean(reportArtifact),
  });

  if (!runId) {
    return (
      <section className="report-pane">
        <header className="report-pane__header">
          <div>
            <div className="eyebrow">Research report</div>
            <h2 className="display-heading report-pane__title">Research report</h2>
            <div className="meta-line">Run progress and the generated report appear here.</div>
          </div>
        </header>
        <div className="report-pane__content">
          <div className="report-pane__empty">
            <strong className="report-pane__empty-title">No report yet</strong>
            <p className="report-pane__empty-copy">
              Start research from the composer to stream progress and render the report here.
            </p>
          </div>
        </div>
      </section>
    );
  }

  const reportMarkdown = normalizeReportMarkdown(report.data?.text);
  const reportTitle =
    extractReportTitle(reportMarkdown) ??
    conversationTitle?.trim() ??
    "Research report";
  const reportBody = stripReportTitle(reportMarkdown);
  const runStatus = run.data?.status;

  async function handleDownload() {
    if (!reportArtifact) return;
    const result = await download.mutateAsync(reportArtifact);
    downloadBlob(result.blob, result.filename);
  }

  return (
    <section className="report-pane">
      <header className="report-pane__header">
        <div>
          <div className="eyebrow">Research report</div>
          <h2 className="display-heading report-pane__title">{reportTitle}</h2>
          <div className="meta-line">
            {run.data
              ? `${run.data.display_status} | ${run.data.display_stage}`
              : "Waiting for run state"}
          </div>
        </div>
        <div className="report-pane__actions">
          {runStatus ? (
            <span className={reportStatusClass(runStatus)}>
              {run.data?.display_status ?? "Running"}
            </span>
          ) : null}
          <Link to={`/runs/${runId}/artifacts`}>
            <Button compact variant="ghost">
              Open review
            </Button>
          </Link>
          <Button
            compact
            variant="secondary"
            onClick={() => void handleDownload()}
            disabled={!reportArtifact}
            loading={download.isPending}
          >
            Download report
          </Button>
        </div>
      </header>

      <div className="report-pane__content">
        <div className="report-pane__body">
          <div className="report-pane__progress">
            <RunProgressCard runId={runId} />
          </div>

          {artifacts.error ? <ErrorBanner body="Run artifacts could not be loaded." /> : null}
          {report.error ? <ErrorBanner body="Report artifact could not be loaded." /> : null}

          {report.isLoading ? (
            <div className="report-pane__empty">
              <strong className="report-pane__empty-title">Loading report</strong>
              <p className="report-pane__empty-copy">
                Fetching the latest markdown artifact for this run.
              </p>
            </div>
          ) : reportBody ? (
            <article className="report-pane__document" data-testid="report-document">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={reportMarkdownComponents}
              >
                {reportBody}
              </ReactMarkdown>
            </article>
          ) : (
            <div className="report-pane__empty">
              <strong className="report-pane__empty-title">Report pending</strong>
              <p className="report-pane__empty-copy">
                {runStatus && !["succeeded", "failed", "canceled"].includes(runStatus)
                  ? "The report will appear here as soon as the export artifact is written."
                  : "This run does not have a markdown report artifact yet."}
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
