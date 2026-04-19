import { useEffect, useMemo, useState } from "react";

import {
  useArtifactDownloadMutation,
  useArtifactsQuery,
  useArtifactTextQuery,
} from "../../entities/artifact/artifact.api";
import { useRunQuery } from "../../entities/run/run.api";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { ReportExportModal } from "./ReportExportModal";
import { ReportPaneView } from "./ReportPaneView";
import { ReportShareModal } from "./ReportShareModal";
import { saveBlob } from "./reportPane.download";
import { deriveReportExportOptions, type ReportExportOption } from "./reportExportOptions";
import { isReportCleared, setReportCleared } from "./reportPane.storage";
import { extractReportTitle, normalizeReportMarkdown, stripReportTitle } from "./reportMarkdown";

type ReportPaneProps = {
  runId?: string | null;
  conversationId: string;
  conversationTitle?: string;
};

function getReportStatusClassName(status?: string) {
  if (status === "succeeded") return "legacy-report-pane__status--success";
  if (status === "failed" || status === "canceled") return "legacy-report-pane__status--danger";
  return "legacy-report-pane__status--warning";
}

function useReportDismissal(conversationId: string, runId?: string | null) {
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    setDismissed(isReportCleared(conversationId, runId));
  }, [conversationId, runId]);

  function dismiss() {
    if (!runId) return;
    setReportCleared(conversationId, runId);
    setDismissed(true);
  }

  return { dismissed, dismiss };
}

export function ReportPane({ runId, conversationId, conversationTitle }: ReportPaneProps) {
  const run = useRunQuery(runId ?? "");
  const artifacts = useArtifactsQuery(runId ?? "", {
    enabled: Boolean(runId),
    refetchInterval:
      run.data && ["succeeded", "failed", "canceled"].includes(run.data.status) ? false : 2500,
  });
  const download = useArtifactDownloadMutation();
  const [exportOpen, setExportOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const { dismissed, dismiss } = useReportDismissal(conversationId, runId);

  const reportArtifact = useMemo(
    () =>
      (artifacts.data ?? []).find(
        (artifact) =>
          artifact.kind === "report_markdown" || artifact.media_type === "text/markdown",
      ) ?? null,
    [artifacts.data],
  );
  const report = useArtifactTextQuery(reportArtifact?.id ?? "", reportArtifact?.filename, {
    enabled: Boolean(reportArtifact),
  });
  const exportOptions = useMemo(
    () => deriveReportExportOptions(artifacts.data ?? []),
    [artifacts.data],
  );

  const reportMarkdown = normalizeReportMarkdown(report.data?.text);
  const reportTitle =
    extractReportTitle(reportMarkdown) ?? conversationTitle?.trim() ?? "Research report";
  const reportBody = stripReportTitle(reportMarkdown);
  const reportStatus = run.data?.status;

  async function handleExport(option: ReportExportOption) {
    if (!option.artifact) return;
    const result = await download.mutateAsync(option.artifact);
    saveBlob(result.blob, result.filename);
    setExportOpen(false);
  }

  return (
    <>
      {artifacts.error ? <ErrorBanner body="Run artifacts could not be loaded." /> : null}
      {report.error ? <ErrorBanner body="Report artifact could not be loaded." /> : null}
      <ReportPaneView
        runId={runId}
        conversationTitle={conversationTitle ?? "Research report"}
        reportTitle={reportTitle}
        reportStatusLabel={run.data?.display_status ?? "Idle"}
        reportStatusClassName={getReportStatusClassName(reportStatus)}
        reportBody={reportBody}
        showToolbar={Boolean(runId || reportBody)}
        dismissed={dismissed}
        loading={report.isLoading}
        onExport={() => setExportOpen(true)}
        onClear={dismiss}
        onShare={() => setShareOpen(true)}
      />
      <ReportExportModal
        open={exportOpen}
        options={exportOptions}
        onClose={() => setExportOpen(false)}
        onExport={(option) => void handleExport(option)}
      />
      <ReportShareModal
        open={shareOpen}
        shareUrl={window.location.href}
        onClose={() => setShareOpen(false)}
      />
    </>
  );
}
