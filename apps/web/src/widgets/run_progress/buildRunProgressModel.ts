import type { RunEventResponse, RunSummaryResponse } from "@researchlens/api-client";
import type {
  ResearchProgressCardModel,
  ResearchProgressEventRow,
  ResearchProgressStatus,
  ResearchProgressStepState,
} from "./runProgress.types";

const STEP_ORDER = ["outline", "retrieve", "evidence_pack", "draft", "evaluate", "export"] as const;
const STEP_LABELS = [
  "Plan the report structure and sections.",
  "Search papers and rank the best sources.",
  "Find supporting snippets for each section.",
  "Write each section with citations.",
  "Check quality and fix weak sections.",
  "Export the final report.",
];

function isTerminalEvent(event: RunEventResponse) {
  return (
    event.audience === "state" &&
    ["run.succeeded", "run.failed", "run.canceled"].includes(event.event_type)
  );
}

function getVisibleEvents(events: RunEventResponse[]) {
  return events.filter((event) => event.audience === "progress" || isTerminalEvent(event));
}

function getProgressStatus(run: RunSummaryResponse): ResearchProgressStatus {
  if (run.status === "failed") return "failed";
  if (run.status === "canceled") return "canceled";
  if (run.status === "succeeded") return "succeeded";
  return run.can_retry ? "blocked" : "running";
}

function hasDraftSectionActivity(events: RunEventResponse[]) {
  return events.some(
    (event) =>
      event.stage === "draft" &&
      (event.message.includes("Draft section") || event.payload?.["section_id"]),
  );
}

function getRetrievePhase(events: RunEventResponse[]) {
  return events.some(
    (event) =>
      event.stage === "retrieve" &&
      (event.message.includes("provider search") || event.message.includes("summary")),
  )
    ? "retrieve"
    : "outline";
}

function getCurrentStepKey(run: RunSummaryResponse, events: RunEventResponse[]) {
  if (run.status === "queued") return "outline";
  if (run.status === "succeeded") return "export";
  if (run.current_stage === "retrieve") return getRetrievePhase(events);
  if (run.current_stage === "draft") {
    return hasDraftSectionActivity(events) ? "draft" : "evidence_pack";
  }
  if (["evaluate", "repair", "validate", "factcheck"].includes(run.current_stage ?? "")) {
    return "evaluate";
  }
  if (run.current_stage === "export") return "export";
  return "outline";
}

function getCurrentStepIndex(run: RunSummaryResponse, events: RunEventResponse[]) {
  return Math.max(STEP_ORDER.indexOf(getCurrentStepKey(run, events)), 0);
}

function buildStepState(
  index: number,
  currentIndex: number,
  status: ResearchProgressStatus,
): ResearchProgressStepState {
  if (status === "succeeded" || index < currentIndex) return "complete";
  if (index === currentIndex) return "current";
  return "pending";
}

function buildStepMetrics(events: RunEventResponse[], status: ResearchProgressStatus) {
  const retrievalSummary = events.find((event) => event.message === "Retrieval summary completed");
  const outlineCount = retrievalSummary?.payload?.["outline_sections"];
  const plannedQueries = retrievalSummary?.payload?.["planned_queries"];
  const selectedSources = retrievalSummary?.payload?.["selected_sources"];
  const evidenceReady = events.filter(
    (event) => event.message === "Draft evidence pack ready",
  ).length;
  const draftedSections = events.filter(
    (event) => event.message === "Draft section completed",
  ).length;
  const evaluationSummary = events.find((event) => event.message.includes("Evaluation completed"));
  const evaluatedCount = evaluationSummary?.payload?.["evaluated_section_count"];
  const sectionCount = evaluationSummary?.payload?.["section_count"];
  const exportSummary = events.find((event) => event.message === "Artifact export completed");
  const artifactCount = exportSummary?.payload?.["artifact_count"];
  return [
    typeof outlineCount === "number" ? `${outlineCount} sections` : null,
    typeof plannedQueries === "number" && typeof selectedSources === "number"
      ? `${plannedQueries} queries | ${selectedSources} selected`
      : null,
    evidenceReady > 0 ? `${evidenceReady} sections` : null,
    draftedSections > 0 ? `${draftedSections} sections` : null,
    typeof evaluatedCount === "number" && typeof sectionCount === "number"
      ? `${evaluatedCount} / ${sectionCount} reviewed`
      : null,
    status === "succeeded"
      ? "done"
      : typeof artifactCount === "number"
        ? `${artifactCount} artifacts`
        : null,
  ];
}

function buildEventDetail(event: RunEventResponse) {
  const payload = event.payload ?? {};
  if (typeof payload["section_title"] === "string") return payload["section_title"];
  if (typeof payload["section_id"] === "string") return payload["section_id"];
  if (typeof payload["reason"] === "string") return payload["reason"];
  if (typeof payload["artifact_count"] === "number")
    return `${payload["artifact_count"]} artifacts`;
  return undefined;
}

function toEventRow(event: RunEventResponse): ResearchProgressEventRow {
  return {
    id: `${event.event_number}`,
    ts: event.ts,
    message: event.message,
    detail: buildEventDetail(event),
    level: event.level as ResearchProgressEventRow["level"],
  };
}

function buildSummaryText(run: RunSummaryResponse, currentAction: ResearchProgressEventRow | null) {
  if (run.status === "succeeded") return "Report completed and ready to review.";
  if (run.status === "failed") return "Research run failed before completion.";
  if (run.status === "canceled") return "Research run stopped before finishing.";
  return currentAction?.message ?? run.display_stage;
}

function buildMetricText(
  status: ResearchProgressStatus,
  stepMetrics: Array<string | null>,
  currentIndex: number,
) {
  if (status === "succeeded") return "Done";
  if (status === "failed" || status === "blocked") return "Needs retry";
  if (status === "canceled") return "Stopped";
  return stepMetrics[currentIndex] ?? "";
}

function buildProgressRatio(status: ResearchProgressStatus, currentIndex: number) {
  if (status === "succeeded") return 1;
  const base = (currentIndex + 0.42) / STEP_ORDER.length;
  if (status === "failed" || status === "blocked" || status === "canceled") {
    return Math.max(0.1, Math.min(0.94, base));
  }
  return Math.max(0.08, Math.min(0.94, base + 0.06));
}

function buildFallbackEvent(run: RunSummaryResponse): RunEventResponse {
  return {
    run_id: run.id,
    event_number: run.last_event_number,
    event_type: "run.running",
    audience: "state",
    level: "info",
    status: run.status,
    stage: run.current_stage,
    display_status: run.display_status,
    display_stage: run.display_stage,
    message: run.display_stage,
    retry_count: run.retry_count,
    cancel_requested: run.cancel_requested,
    payload: null,
    ts: run.updated_at,
  };
}

export function buildRunProgressModel(
  run: RunSummaryResponse,
  events: RunEventResponse[],
  conversationTitle?: string,
): ResearchProgressCardModel {
  const visibleEvents = getVisibleEvents(events);
  const status = getProgressStatus(run);
  const currentIndex = getCurrentStepIndex(run, visibleEvents);
  const stepMetrics = buildStepMetrics(visibleEvents, status);
  const latestEvent = visibleEvents.at(-1) ?? events.at(-1) ?? buildFallbackEvent(run);
  const currentAction = status === "running" ? toEventRow(latestEvent) : null;
  const recentEvents = visibleEvents
    .filter((event) => !["stage.started", "stage.completed"].includes(event.event_type))
    .slice(-6)
    .reverse()
    .map(toEventRow);

  return {
    title: conversationTitle?.trim() || "Research report",
    status,
    steps: STEP_ORDER.map((step, index) => ({
      id: step,
      label: STEP_LABELS[index],
      state: buildStepState(index, currentIndex, status),
    })),
    stepMetrics,
    summaryText: buildSummaryText(run, currentAction),
    metricText: buildMetricText(status, stepMetrics, currentIndex),
    progressRatio: buildProgressRatio(status, currentIndex),
    currentAction,
    recentEvents,
  };
}
