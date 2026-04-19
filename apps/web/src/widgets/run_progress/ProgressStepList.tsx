import { motion } from "framer-motion";
import { Check } from "lucide-react";

import type { ResearchProgressCardModel } from "./runProgress.types";
import { WaveText } from "./WaveText";

type ProgressStepListProps = {
  steps: ResearchProgressCardModel["steps"];
  stepMetrics: ResearchProgressCardModel["stepMetrics"];
  status: ResearchProgressCardModel["status"];
};

function StepBadge({
  index,
  state,
  failed,
}: {
  index: number;
  state: ResearchProgressCardModel["steps"][number]["state"];
  failed: boolean;
}) {
  if (state === "complete") {
    return (
      <span className="legacy-progress-step__badge legacy-progress-step__badge--complete">
        <Check className="legacy-progress-step__check" />
      </span>
    );
  }
  if (failed && state === "current") {
    return (
      <span className="legacy-progress-step__badge legacy-progress-step__badge--failed">x</span>
    );
  }
  if (state === "current") {
    return (
      <motion.span
        className="legacy-progress-step__badge legacy-progress-step__badge--current"
        animate={{ boxShadow: ["0 0 0 0 rgba(255,255,255,.7)", "0 0 0 8px rgba(255,255,255,0)"] }}
        transition={{ duration: 2, ease: "easeOut", repeat: Infinity }}
      >
        {index}
      </motion.span>
    );
  }
  return (
    <span className="legacy-progress-step__badge legacy-progress-step__badge--pending">
      {index}
    </span>
  );
}

export function ProgressStepList({ steps, stepMetrics, status }: ProgressStepListProps) {
  return (
    <div className="legacy-progress-step-list">
      {steps.map((step, index) => (
        <div key={step.id} className="legacy-progress-step">
          <div className="legacy-progress-step__rail">
            <StepBadge index={index + 1} state={step.state} failed={status !== "running"} />
            {index < steps.length - 1 ? <div className="legacy-progress-step__connector" /> : null}
          </div>
          <div className="legacy-progress-step__copy">
            <p className="legacy-progress-step__label">
              {step.state === "current" && status === "running" ? (
                <WaveText text={step.label} duration={2.8} />
              ) : (
                step.label
              )}
            </p>
            <span className="legacy-progress-step__metric">{stepMetrics[index] ?? "—"}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
