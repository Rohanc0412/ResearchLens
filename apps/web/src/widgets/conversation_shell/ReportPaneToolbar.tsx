import { Sparkles } from "lucide-react";

type ReportPaneToolbarProps = {
  active: boolean;
  onExport: () => void;
  onClear: () => void;
  onShare: () => void;
};

export function ReportPaneToolbar({ active, onExport, onClear, onShare }: ReportPaneToolbarProps) {
  if (!active) return null;

  return (
    <div className="legacy-report-toolbar">
      <button onClick={onExport} className="legacy-report-toolbar__button">
        Export
      </button>
      <button onClick={onClear} className="legacy-report-toolbar__button">
        Clear
      </button>
      <button onClick={onShare} className="legacy-report-toolbar__button">
        Share
      </button>
      <div className="legacy-report-toolbar__accent">
        <Sparkles className="legacy-report-toolbar__accent-icon" />
      </div>
    </div>
  );
}
