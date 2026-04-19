import { buildRunProgressModel } from "./buildRunProgressModel";

function buildRun(overrides?: Partial<Parameters<typeof buildRunProgressModel>[0]>) {
  return {
    id: "run-1",
    project_id: "project-1",
    conversation_id: "conversation-1",
    status: "running",
    current_stage: "retrieve",
    output_type: "report",
    client_request_id: null,
    retry_count: 0,
    cancel_requested: false,
    created_at: "2026-04-17T15:00:00Z",
    updated_at: "2026-04-17T15:01:00Z",
    started_at: "2026-04-17T15:00:05Z",
    finished_at: null,
    failure_reason: null,
    error_code: null,
    last_event_number: 2,
    display_status: "Running",
    display_stage: "Searching for sources",
    can_stop: true,
    can_retry: false,
    ...overrides,
  };
}

function buildEvent(overrides?: Partial<Parameters<typeof buildRunProgressModel>[1][number]>) {
  return {
    run_id: "run-1",
    event_number: 1,
    event_type: "checkpoint.written",
    audience: "progress",
    level: "info",
    status: "running",
    stage: "retrieve",
    display_status: "Running",
    display_stage: "Searching for sources",
    message: "Retrieval summary completed",
    retry_count: 0,
    cancel_requested: false,
    payload: {
      outline_sections: 5,
      planned_queries: 4,
      selected_sources: 9,
    },
    ts: "2026-04-17T15:01:00Z",
    ...overrides,
  };
}

test("maps retrieval progress into the old six-step model", () => {
  const model = buildRunProgressModel(buildRun(), [buildEvent()], "Cancer biomarkers");

  expect(model.title).toBe("Cancer biomarkers");
  expect(model.steps[1]?.state).toBe("current");
  expect(model.stepMetrics[0]).toBe("5 sections");
  expect(model.stepMetrics[1]).toBe("4 queries | 9 selected");
  expect(model.currentAction?.message).toBe("Retrieval summary completed");
});

test("marks successful runs as complete", () => {
  const model = buildRunProgressModel(
    buildRun({
      status: "succeeded",
      current_stage: "export",
      display_status: "Completed",
      can_stop: false,
    }),
    [
      buildEvent({
        message: "Artifact export completed",
        stage: "export",
        payload: { artifact_count: 3 },
      }),
    ],
    "Cancer biomarkers",
  );

  expect(model.status).toBe("succeeded");
  expect(model.progressRatio).toBe(1);
  expect(model.metricText).toBe("Done");
  expect(model.steps.at(-1)?.state).toBe("complete");
});
