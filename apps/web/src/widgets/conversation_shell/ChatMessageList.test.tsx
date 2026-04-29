import { createRef } from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { ChatMessageList } from "./ChatMessageList";

const useRunQueryMock = vi.fn();
const useArtifactsQueryMock = vi.fn();
const mutateAsyncMock = vi.fn();

vi.mock("../../entities/run/run.api", () => ({
  useRunQuery: (runId: string) => useRunQueryMock(runId),
}));

vi.mock("../../entities/artifact/artifact.api", () => ({
  useArtifactsQuery: (...args: unknown[]) => useArtifactsQueryMock(...args),
  useArtifactDownloadMutation: () => ({ mutateAsync: mutateAsyncMock }),
}));

function buildRunStartedMessage() {
  return {
    id: "assistant-run",
    role: "assistant" as const,
    type: "run_started" as const,
    content_text: "Starting the research pipeline.",
    content_json: { run_id: "run-1" },
    created_at: "2026-04-19T12:00:00Z",
  };
}

function renderList(activeRunId?: string | null) {
  return render(
    <MemoryRouter>
      <ChatMessageList
        messages={[buildRunStartedMessage()]}
        isTyping={false}
        webSearching={false}
        isActionPending={false}
        activeRunId={activeRunId}
        messagesEndRef={createRef<HTMLDivElement>()}
        onAction={() => {}}
      />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  useRunQueryMock.mockReset();
  useArtifactsQueryMock.mockReset();
  mutateAsyncMock.mockReset();
  useRunQueryMock.mockReturnValue({
    data: { status: "succeeded", display_status: "Completed" },
  });
  useArtifactsQueryMock.mockReturnValue({
    data: [
      {
        id: "artifact-1",
        run_id: "run-1",
        kind: "final_report_markdown",
        filename: "report.md",
        media_type: "text/markdown; charset=utf-8",
        storage_backend: "disk",
        byte_size: 128,
        sha256: "abc",
        created_at: "2026-04-19T12:01:00Z",
        manifest_id: null,
      },
    ],
  });
});

test("shows the completed artifact card in the chat timeline when artifacts exist", () => {
  renderList("run-1");

  expect(screen.getByText("Research report")).toBeInTheDocument();
  expect(screen.getByText("Run completed")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Download .md" })).toBeVisible();
  expect(screen.getByRole("link", { name: "View all artifacts" })).toBeVisible();
});

test("shows the tracking note for the active run before artifacts exist", () => {
  useRunQueryMock.mockReturnValue({
    data: { status: "running", display_status: "Running" },
  });
  useArtifactsQueryMock.mockReturnValue({
    data: [],
  });

  renderList("run-1");

  expect(screen.getByText("Tracking progress in the research report panel.")).toBeInTheDocument();
  expect(screen.queryByText("Run completed")).not.toBeInTheDocument();
});
