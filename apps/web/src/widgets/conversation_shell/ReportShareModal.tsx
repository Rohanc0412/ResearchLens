import { useState } from "react";

type ReportShareModalProps = {
  open: boolean;
  shareUrl: string;
  onClose: () => void;
};

export function ReportShareModal({ open, shareUrl, onClose }: ReportShareModalProps) {
  const [copied, setCopied] = useState(false);

  if (!open) return null;

  async function handleCopy() {
    await navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="legacy-report-modal" onClick={onClose}>
      <div className="legacy-report-modal__dialog" onClick={(event) => event.stopPropagation()}>
        <h3 className="legacy-report-modal__title">Share report</h3>
        <p className="legacy-report-modal__copy">
          Share this link with teammates who already have workspace access.
        </p>
        <div className="legacy-report-modal__share-row">
          <input readOnly value={shareUrl} className="legacy-report-modal__share-input" />
          <button onClick={() => void handleCopy()} className="legacy-report-modal__share-button">
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
        <button onClick={onClose} className="legacy-report-modal__close">
          Done
        </button>
      </div>
    </div>
  );
}
