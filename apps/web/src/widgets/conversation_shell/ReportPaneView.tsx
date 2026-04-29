import { RunProgressCard } from "../run_progress/RunProgressCard";
import { ReportSectionView } from "./ReportSectionView";
import type { ReportDocument } from "./reportDocument";
import { ReportPaneToolbar } from "./ReportPaneToolbar";

type ReportPaneViewProps = {
  runId?: string | null;
  conversationTitle: string;
  report: ReportDocument;
  reportStatusLabel: string;
  reportStatusClassName: string;
  isRunning: boolean;
  showToolbar: boolean;
  dismissed: boolean;
  loading: boolean;
  onExport: () => void;
  onClear: () => void;
  onShare: () => void;
  onSectionSave: (sectionId: string, content: string) => void;
};

function renderEmptyState(loading: boolean, dismissed: boolean, showNoReportYet: boolean) {
  if (loading) {
    return (
      <div className="legacy-report-pane__empty">
        <p className="legacy-report-pane__empty-title">Loading report</p>
        <p className="legacy-report-pane__empty-copy">
          Fetching the latest report artifact for this run.
        </p>
      </div>
    );
  }
  if (dismissed) {
    return (
      <div className="legacy-report-pane__empty">
        <p className="legacy-report-pane__empty-title">Report cleared</p>
        <p className="legacy-report-pane__empty-copy">
          This run was cleared from the panel. Start a newer run to render another report here.
        </p>
      </div>
    );
  }
  if (!showNoReportYet) {
    return null;
  }
  return (
    <div className="legacy-report-pane__empty">
      <p className="legacy-report-pane__empty-title">No report yet</p>
      <p className="legacy-report-pane__empty-copy">
        Enable <span className="legacy-report-pane__inline-strong">Run research report</span> in the
        composer and send your question to generate a full report.
      </p>
    </div>
  );
}

export function ReportPaneView({
  runId,
  conversationTitle,
  report,
  reportStatusLabel,
  reportStatusClassName,
  isRunning,
  showToolbar,
  dismissed,
  loading,
  onExport,
  onClear,
  onShare,
  onSectionSave,
}: ReportPaneViewProps) {
  const emptyState = renderEmptyState(loading, dismissed, !runId);

  return (
    <section className={`legacy-report-pane ${isRunning ? "legacy-report-pane--running" : ""}`}>
      <header className="legacy-report-pane__header">
        <div>
          <div className="legacy-report-pane__eyebrow">Research report</div>
          <h2 className="legacy-report-pane__title">{report.title || conversationTitle}</h2>
        </div>
        {(runId || report.sections.length > 0) && (
          <span className={`legacy-report-pane__status ${reportStatusClassName}`}>
            {reportStatusLabel}
          </span>
        )}
      </header>

      <ReportPaneToolbar
        active={showToolbar}
        onExport={onExport}
        onClear={onClear}
        onShare={onShare}
      />

      <div className="legacy-report-pane__content">
        {runId && isRunning ? (
          <RunProgressCard runId={runId} conversationTitle={conversationTitle} />
        ) : null}
        {report.sections.length > 0 && !dismissed ? (
          <article className="legacy-report-pane__document" data-testid="report-document">
            {report.sections.map((section) => (
              <ReportSectionView key={section.id} section={section} onSave={onSectionSave} />
            ))}
          </article>
        ) : emptyState}
      </div>
    </section>
  );
}
