import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { RunProgressCard } from "../run_progress/RunProgressCard";
import { reportMarkdownComponents } from "./reportMarkdown";
import { ReportPaneToolbar } from "./ReportPaneToolbar";

type ReportPaneViewProps = {
  runId?: string | null;
  conversationTitle: string;
  reportTitle: string;
  reportStatusLabel: string;
  reportStatusClassName: string;
  reportBody: string;
  showToolbar: boolean;
  dismissed: boolean;
  loading: boolean;
  onExport: () => void;
  onClear: () => void;
  onShare: () => void;
};

function renderEmptyState(loading: boolean, dismissed: boolean) {
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
  reportTitle,
  reportStatusLabel,
  reportStatusClassName,
  reportBody,
  showToolbar,
  dismissed,
  loading,
  onExport,
  onClear,
  onShare,
}: ReportPaneViewProps) {
  return (
    <section className="legacy-report-pane">
      <header className="legacy-report-pane__header">
        <div>
          <div className="legacy-report-pane__eyebrow">Research report</div>
          <h2 className="legacy-report-pane__title">{reportTitle || conversationTitle}</h2>
        </div>
        {(runId || reportBody) && (
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
        {runId ? <RunProgressCard runId={runId} conversationTitle={conversationTitle} /> : null}
        {reportBody && !dismissed ? (
          <article className="legacy-report-pane__document" data-testid="report-document">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={reportMarkdownComponents}>
              {reportBody}
            </ReactMarkdown>
          </article>
        ) : (
          renderEmptyState(loading, dismissed)
        )}
      </div>
    </section>
  );
}
