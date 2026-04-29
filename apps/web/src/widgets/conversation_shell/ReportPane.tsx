import { useEffect, useMemo, useRef, useState } from "react";

import {
  useArtifactsQuery,
  useArtifactTextQuery,
} from "../../entities/artifact/artifact.api";
import { useRunQuery } from "../../entities/run/run.api";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { ReportExportModal } from "./ReportExportModal";
import { ReportPaneView } from "./ReportPaneView";
import { ReportShareModal } from "./ReportShareModal";
import { EMPTY_REPORT, type ReportDocument } from "./reportDocument";
import { exportReport } from "./reportExport";
import { deriveReportExportOptions, type ReportExportOption } from "./reportExportOptions";
import {
  clearStoredReport,
  isReportCleared,
  loadStoredReport,
  persistStoredReport,
  setReportCleared,
} from "./reportPane.storage";
import { parseReportMarkdown } from "./reportParser";

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
  const [report, setReport] = useState<ReportDocument>(EMPTY_REPORT);
  const [storageReady, setStorageReady] = useState(false);
  const skipPersistRef = useRef(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const { dismissed, dismiss } = useReportDismissal(conversationId, runId);
  const reportStatus = run.data?.status;

  const artifactRefetchInterval =
    !runId
      ? false
      : reportStatus === "succeeded" && report.sections.length === 0
        ? 2500
        : reportStatus && ["succeeded", "failed", "canceled"].includes(reportStatus)
          ? false
          : 2500;
  const artifacts = useArtifactsQuery(runId ?? "", {
    enabled: Boolean(runId),
    refetchInterval: artifactRefetchInterval,
  });

  const reportArtifact = useMemo(
    () =>
      (artifacts.data ?? []).find(
        (artifact) =>
          artifact.kind === "final_report_markdown" ||
          artifact.kind === "report_markdown" ||
          artifact.media_type.toLowerCase().startsWith("text/markdown"),
      ) ?? null,
    [artifacts.data],
  );
  const reportArtifactText = useArtifactTextQuery(reportArtifact?.id ?? "", reportArtifact?.filename, {
    enabled: Boolean(reportArtifact) && storageReady && !dismissed && report.sections.length === 0,
  });
  const exportOptions = useMemo(() => deriveReportExportOptions(), []);

  const isRunning =
    Boolean(runId) && !["succeeded", "failed", "canceled"].includes(reportStatus ?? "");
  const waitingForCompletedReport =
    reportStatus === "succeeded" && !dismissed && report.sections.length === 0;
  const loading =
    waitingForCompletedReport && (!reportArtifact || reportArtifactText.isLoading || !storageReady);

  useEffect(() => {
    skipPersistRef.current = true;
    setStorageReady(false);
    const stored = loadStoredReport(conversationId, runId);
    setReport(
      stored ?? {
        ...EMPTY_REPORT,
        title: conversationTitle?.trim() || EMPTY_REPORT.title,
      },
    );
    setStorageReady(true);
  }, [conversationId, conversationTitle, runId]);

  useEffect(() => {
    if (!conversationId || !runId || !storageReady) return;
    if (skipPersistRef.current) {
      skipPersistRef.current = false;
      return;
    }
    persistStoredReport(conversationId, runId, report);
  }, [conversationId, report, runId, storageReady]);

  useEffect(() => {
    if (!runId || !storageReady || dismissed || report.sections.length > 0) return;
    const markdown = reportArtifactText.data?.text;
    if (!markdown) return;
    const nextReport = parseReportMarkdown(markdown, conversationTitle);
    if (nextReport.sections.length === 0) return;
    setReport(nextReport);
  }, [
    conversationTitle,
    dismissed,
    report.sections.length,
    reportArtifactText.data?.text,
    runId,
    storageReady,
  ]);

  async function handleExport(option: ReportExportOption) {
    await exportReport(report, option.id);
    setExportOpen(false);
  }

  function handleSectionSave(sectionId: string, content: string) {
    const blocks = content
      .split(/\n{2,}/)
      .map((item) => item.trim())
      .filter(Boolean)
      .map((item) => ({
        text: item,
      }));

    setReport((current) => ({
      ...current,
      sections: current.sections.map((section) =>
        section.id === sectionId ? { ...section, content: blocks } : section,
      ),
    }));
  }

  function handleClear() {
    if (!runId) return;
    clearStoredReport(conversationId, runId);
    setReport({
      ...EMPTY_REPORT,
      title: conversationTitle?.trim() || EMPTY_REPORT.title,
    });
    dismiss();
  }

  return (
    <>
      {artifacts.error ? <ErrorBanner body="Run artifacts could not be loaded." /> : null}
      {reportArtifactText.error ? <ErrorBanner body="Report artifact could not be loaded." /> : null}
      <ReportPaneView
        runId={runId}
        conversationTitle={conversationTitle ?? "Research report"}
        report={report}
        reportStatusLabel={run.data?.display_status ?? "Idle"}
        reportStatusClassName={getReportStatusClassName(reportStatus)}
        isRunning={isRunning}
        showToolbar={Boolean(runId || report.sections.length > 0)}
        dismissed={dismissed}
        loading={loading}
        onExport={() => setExportOpen(true)}
        onClear={handleClear}
        onShare={() => setShareOpen(true)}
        onSectionSave={handleSectionSave}
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
