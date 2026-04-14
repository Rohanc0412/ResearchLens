import type { RunEventResponse, RunSummaryResponse } from "@researchlens/api-client";

const stageOrder = ["queued", "retrieve", "draft", "evaluate", "repair", "export", "complete"];

const stageLabels: Record<string, { title: string; body: string }> = {
  queued: { title: "Queued", body: "Run accepted and waiting for execution." },
  retrieve: { title: "Retrieve", body: "Collecting source material and evidence chunks." },
  draft: { title: "Draft", body: "Synthesizing the working research report." },
  evaluate: { title: "Evaluate", body: "Checking claims, citations, and quality signals." },
  repair: { title: "Repair", body: "Reworking sections that need stronger evidence." },
  export: { title: "Export", body: "Packaging final artifacts and manifests." },
  complete: { title: "Complete", body: "Run settled and ready for review." },
};

const terminalStatuses = new Set(["succeeded", "failed", "canceled"]);

function normalizeStage(run: RunSummaryResponse) {
  if (run.status === "queued") return "queued";
  if (terminalStatuses.has(run.status)) return "complete";
  return run.current_stage ?? "queued";
}

export function buildRunProgressModel(run: RunSummaryResponse, events: RunEventResponse[]) {
  const currentStage = normalizeStage(run);
  const currentIndex = Math.max(stageOrder.indexOf(currentStage), 0);
  const isTerminal = terminalStatuses.has(run.status);
  const progress =
    run.status === "failed" || run.status === "canceled"
      ? 100
      : Math.min(100, Math.round(((currentIndex + (isTerminal ? 1 : 0.45)) / stageOrder.length) * 100));

  return {
    currentAction: events.at(-1)?.message ?? run.display_stage,
    currentStage,
    isTerminal,
    progress,
    recentEvents: [...events].slice(-10).reverse(),
    steps: stageOrder.map((stage, index) => {
      const state =
        run.status === "failed" && stage === currentStage
          ? "failed"
          : run.status === "canceled" && stage === currentStage
            ? "canceled"
            : index < currentIndex || (isTerminal && stage === "complete")
              ? "done"
              : index === currentIndex
                ? "active"
                : "pending";

      return {
        ...stageLabels[stage],
        key: stage,
        state,
      };
    }),
  };
}
