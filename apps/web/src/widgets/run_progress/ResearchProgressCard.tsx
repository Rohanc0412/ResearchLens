import { motion } from "framer-motion";
import { ChevronDown, ChevronUp, ExternalLink, RotateCcw } from "lucide-react";

import type { ResearchProgressCardModel } from "./runProgress.types";
import { ProgressEventLog } from "./ProgressEventLog";
import { ProgressStepList } from "./ProgressStepList";
import { WaveText } from "./WaveText";

type ResearchProgressCardProps = {
  model: ResearchProgressCardModel;
  expanded: boolean;
  onToggleExpanded: () => void;
  onCancel?: () => void;
  onRetry?: () => void;
  runId?: string;
};

export function ResearchProgressCard({
  model,
  expanded,
  onToggleExpanded,
  onCancel,
  onRetry,
  runId,
}: ResearchProgressCardProps) {
  const retryable = model.status === "failed" || model.status === "blocked";

  return (
    <section className="legacy-progress-card">
      <div className="legacy-progress-card__header">
        <div>
          <h3 className="legacy-progress-card__title">{model.title}</h3>
          <p className="legacy-progress-card__subtitle">
            {retryable
              ? "Run failed - review or retry"
              : model.status === "succeeded"
                ? "Report complete"
                : "Live research progress"}
          </p>
        </div>
        <button onClick={onToggleExpanded} className="legacy-progress-card__updates">
          Updates{" "}
          {expanded ? (
            <ChevronUp className="legacy-progress-card__icon" />
          ) : (
            <ChevronDown className="legacy-progress-card__icon" />
          )}
        </button>
      </div>

      <ProgressStepList steps={model.steps} stepMetrics={model.stepMetrics} status={model.status} />

      <div className="legacy-progress-card__summary">
        <p className="legacy-progress-card__summary-text">
          {model.status === "running" ? (
            <WaveText
              text={model.summaryText}
              duration={3.2}
              className="legacy-progress-card__summary-wave"
            />
          ) : (
            model.summaryText
          )}
        </p>
        <span className="legacy-progress-card__metric">{model.metricText}</span>
      </div>

      <div className="legacy-progress-card__footer">
        <div className="legacy-progress-card__bar">
          <motion.div
            className="legacy-progress-card__fill"
            style={{ width: `${Math.max(6, Math.round(model.progressRatio * 100))}%` }}
            animate={model.status === "running" ? { opacity: [0.7, 1, 0.7] } : undefined}
            transition={{ duration: 2.2, ease: "linear", repeat: Infinity }}
          />
        </div>
        {model.status === "running" && onCancel ? (
          <button
            onClick={onCancel}
            aria-label="Stop research run"
            className="legacy-progress-card__action"
          >
            <span className="legacy-progress-card__stop-square" />
          </button>
        ) : null}
        {retryable && onRetry ? (
          <button onClick={onRetry} className="legacy-progress-card__retry">
            <RotateCcw className="legacy-progress-card__retry-icon" /> Retry
          </button>
        ) : null}
      </div>

      {model.status === "succeeded" && runId ? (
        <a
          href={`/runs/${encodeURIComponent(runId)}/artifacts`}
          className="legacy-progress-card__artifacts-link"
        >
          <ExternalLink className="legacy-progress-card__retry-icon" /> View Artifacts
        </a>
      ) : null}

      <ProgressEventLog
        expanded={expanded}
        currentAction={model.currentAction}
        events={model.recentEvents}
      />
    </section>
  );
}
