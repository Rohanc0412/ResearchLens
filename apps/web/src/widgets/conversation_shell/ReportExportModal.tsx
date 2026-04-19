import type { ReportExportOption } from "./reportExportOptions";

type ReportExportModalProps = {
  open: boolean;
  options: ReportExportOption[];
  onClose: () => void;
  onExport: (option: ReportExportOption) => void;
};

export function ReportExportModal({ open, options, onClose, onExport }: ReportExportModalProps) {
  if (!open) return null;

  return (
    <div className="legacy-report-modal" onClick={onClose}>
      <div className="legacy-report-modal__dialog" onClick={(event) => event.stopPropagation()}>
        <h3 className="legacy-report-modal__title">Export report</h3>
        <div className="legacy-report-modal__options">
          {options.map((option) => (
            <button
              key={option.id}
              onClick={() => onExport(option)}
              disabled={!option.artifact}
              className="legacy-report-modal__option"
            >
              <span className="legacy-report-modal__option-label">{option.label}</span>
              <span className="legacy-report-modal__option-description">
                {option.artifact ? option.description : "Not available for this run"}
              </span>
            </button>
          ))}
        </div>
        <button onClick={onClose} className="legacy-report-modal__close">
          Cancel
        </button>
      </div>
    </div>
  );
}
