import { describe, expect, test } from "vitest";

import type { ChatMessage } from "../../entities/chat/chat.types";
import { extractLatestRunId, resolveReportRunId } from "./reportRunSelection";

function buildRunMessage(runId: string): ChatMessage {
  return {
    id: `message:${runId}`,
    role: "assistant",
    type: "run_started",
    content_text: "Run started",
    content_json: { run_id: runId },
    created_at: "2026-04-17T15:00:00Z",
  };
}

describe("reportRunSelection", () => {
  test("extracts the latest run_started id from message history", () => {
    expect(extractLatestRunId([buildRunMessage("run-1"), buildRunMessage("run-2")])).toBe(
      "run-2",
    );
  });

  test("resolves run id by url, then messages, then local storage", () => {
    localStorage.setItem("researchlens:last-run:conversation-1", "stored-run");

    expect(
      resolveReportRunId({
        urlRunId: "url-run",
        messages: [buildRunMessage("message-run")],
        conversationId: "conversation-1",
      }),
    ).toBe("url-run");

    expect(
      resolveReportRunId({
        urlRunId: null,
        messages: [buildRunMessage("message-run")],
        conversationId: "conversation-1",
      }),
    ).toBe("message-run");

    expect(
      resolveReportRunId({
        urlRunId: null,
        messages: [],
        conversationId: "conversation-1",
      }),
    ).toBe("stored-run");
  });
});
