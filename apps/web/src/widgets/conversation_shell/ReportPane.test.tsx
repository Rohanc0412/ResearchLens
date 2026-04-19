import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { ReportPane } from "./ReportPane";

const useRunQueryMock = vi.fn();
const useArtifactsQueryMock = vi.fn();
const useArtifactTextQueryMock = vi.fn();
const mutateAsyncMock = vi.fn();

vi.mock("../../entities/run/run.api", () => ({
  useRunQuery: (runId: string) => useRunQueryMock(runId),
}));

vi.mock("../../entities/artifact/artifact.api", () => ({
  useArtifactsQuery: (...args: unknown[]) => useArtifactsQueryMock(...args),
  useArtifactTextQuery: (...args: unknown[]) => useArtifactTextQueryMock(...args),
  useArtifactDownloadMutation: () => ({ mutateAsync: mutateAsyncMock }),
}));

vi.mock("../run_progress/RunProgressCard", () => ({
  RunProgressCard: () => <div>Progress card</div>,
}));

function buildArtifact(
  overrides?: Partial<{ id: string; filename: string; media_type: string; kind: string }>,
) {
  return {
    id: "artifact-md",
    run_id: "run-1",
    kind: "report_markdown",
    filename: "report.md",
    media_type: "text/markdown",
    storage_backend: "disk",
    byte_size: 12,
    sha256: "hash",
    created_at: "2026-04-17T15:00:00Z",
    manifest_id: null,
    ...overrides,
  };
}

beforeEach(() => {
  localStorage.clear();
  mutateAsyncMock.mockReset();
  HTMLAnchorElement.prototype.click = vi.fn();
  URL.createObjectURL = vi.fn(() => "blob:test");
  URL.revokeObjectURL = vi.fn();
  useRunQueryMock.mockImplementation((runId?: string) => ({
    data: runId ? { status: "succeeded", display_status: "Completed" } : undefined,
  }));
  useArtifactsQueryMock.mockImplementation((runId?: string) => ({
    data: runId ? [buildArtifact()] : [],
  }));
  useArtifactTextQueryMock.mockImplementation((artifactId?: string) => ({
    data: artifactId ? { text: "# Research report\n\nBody copy" } : undefined,
    isLoading: false,
  }));
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: { writeText: vi.fn().mockResolvedValue(undefined) },
  });
});

test("shows the old empty state when no run is selected", () => {
  render(<ReportPane conversationId="conversation-1" conversationTitle="Thread" />);

  expect(screen.getByText(/No report yet/i)).toBeInTheDocument();
  expect(screen.queryByText("Export")).not.toBeInTheDocument();
});

test("exports only available run artifacts from the toolbar", async () => {
  const user = userEvent.setup();
  mutateAsyncMock.mockResolvedValue({
    blob: new Blob(["report"]),
    filename: "report.md",
  });

  render(<ReportPane runId="run-1" conversationId="conversation-1" conversationTitle="Thread" />);

  await user.click(screen.getByRole("button", { name: "Export" }));
  expect(screen.getByRole("button", { name: /PDF document/i })).toBeDisabled();
  await user.click(screen.getByRole("button", { name: /Markdown/i }));

  await waitFor(() => expect(mutateAsyncMock).toHaveBeenCalledWith(buildArtifact()));
});

test("clears the report for the active run", async () => {
  const user = userEvent.setup();

  render(<ReportPane runId="run-1" conversationId="conversation-1" conversationTitle="Thread" />);

  await user.click(screen.getByRole("button", { name: "Clear" }));

  expect(screen.getByText("Report cleared")).toBeInTheDocument();
  expect(localStorage.getItem("researchlens:report-cleared:conversation-1:run-1")).toBe("1");
});
