export type ResearchProgressStatus = "running" | "blocked" | "failed" | "succeeded" | "canceled";
export type ResearchProgressStepState = "complete" | "current" | "pending";

export type ResearchProgressStep = {
  id: string;
  label: string;
  state: ResearchProgressStepState;
};

export type ResearchProgressEventRow = {
  id: string;
  ts: string;
  message: string;
  detail?: string;
  level: "debug" | "info" | "warn" | "error";
};

export type ResearchProgressCardModel = {
  title: string;
  status: ResearchProgressStatus;
  steps: ResearchProgressStep[];
  stepMetrics: Array<string | null>;
  summaryText: string;
  metricText: string;
  progressRatio: number;
  currentAction: ResearchProgressEventRow | null;
  recentEvents: ResearchProgressEventRow[];
};
