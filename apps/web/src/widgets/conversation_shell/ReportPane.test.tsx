import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { ReportPane } from "./ReportPane";

const useRunQueryMock = vi.fn();
const useArtifactsQueryMock = vi.fn();
const useArtifactTextQueryMock = vi.fn();
const exportReportMock = vi.fn();

vi.mock("../../entities/run/run.api", () => ({
  useRunQuery: (runId: string) => useRunQueryMock(runId),
}));

vi.mock("../../entities/artifact/artifact.api", () => ({
  useArtifactsQuery: (...args: unknown[]) => useArtifactsQueryMock(...args),
  useArtifactTextQuery: (...args: unknown[]) => useArtifactTextQueryMock(...args),
}));

vi.mock("../run_progress/RunProgressCard", () => ({
  RunProgressCard: () => <div>Progress card</div>,
}));

vi.mock("./reportExport", () => ({
  exportReport: (...args: unknown[]) => exportReportMock(...args),
}));

function buildArtifact(
  overrides?: Partial<{ id: string; filename: string; media_type: string; kind: string }>,
) {
  return {
    id: "artifact-md",
    run_id: "run-1",
    kind: "final_report_markdown",
    filename: "run-1-final-report.md",
    media_type: "text/markdown; charset=utf-8",
    storage_backend: "disk",
    byte_size: 12,
    sha256: "hash",
    created_at: "2026-04-17T15:00:00Z",
    manifest_id: null,
    ...overrides,
  };
}

function buildMarkdown(body = "Body copy") {
  return `# Research report

## Overview

${body}
`;
}

function buildMarkdownFromSections(
  sections: Array<{ heading: string; body: string }>,
) {
  return [
    "# Research report",
    "",
    ...sections.flatMap((section) => [`## ${section.heading}`, "", section.body, ""]),
  ].join("\n");
}

beforeEach(() => {
  localStorage.clear();
  exportReportMock.mockReset();
  useRunQueryMock.mockReset();
  useArtifactsQueryMock.mockReset();
  useArtifactTextQueryMock.mockReset();
  useRunQueryMock.mockImplementation((runId?: string) => ({
    data: runId ? { status: "succeeded", display_status: "Completed" } : undefined,
  }));
  useArtifactsQueryMock.mockImplementation((runId?: string) => ({
    data: runId ? [buildArtifact()] : [],
  }));
  useArtifactTextQueryMock.mockImplementation((artifactId?: string) => ({
    data: artifactId ? { text: buildMarkdown() } : undefined,
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

test("hydrates the current final report artifact and shows section editing", async () => {
  render(<ReportPane runId="run-1" conversationId="conversation-1" conversationTitle="Thread" />);

  expect(await screen.findByText("Overview")).toBeInTheDocument();
  expect(screen.getByTestId("report-document")).toHaveTextContent("Body copy");
  expect(screen.getByRole("button", { name: "Edit" })).toBeVisible();
});

test("renders report sections in markdown order with full legacy headings", async () => {
  useArtifactTextQueryMock.mockImplementation((artifactId?: string) => ({
    data: artifactId
      ? {
          text: buildMarkdownFromSections([
            { heading: "1. Recent Developments", body: "First body" },
            { heading: "2. Challenges", body: "Second body" },
          ]),
        }
      : undefined,
    isLoading: false,
  }));

  render(<ReportPane runId="run-1" conversationId="conversation-1" conversationTitle="Thread" />);

  const headings = await screen.findAllByRole("heading", { level: 3 });

  expect(headings.map((item) => item.textContent)).toEqual([
    "1. Recent Developments",
    "2. Challenges",
  ]);
});

test("exports the current edited report from the toolbar", async () => {
  const user = userEvent.setup();

  render(<ReportPane runId="run-1" conversationId="conversation-1" conversationTitle="Thread" />);

  await user.click(await screen.findByRole("button", { name: "Export" }));
  await user.click(screen.getByRole("button", { name: /Markdown/i }));

  await waitFor(() =>
    expect(exportReportMock).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Research report",
        sections: expect.arrayContaining([
          expect.objectContaining({ heading: "Overview" }),
        ]),
      }),
      "md",
    ),
  );
});

test("keeps polling after success until the markdown artifact appears", async () => {
  let artifactsData: ReturnType<typeof buildArtifact>[] = [];
  useArtifactsQueryMock.mockImplementation((runId?: string) => ({
    data: runId ? artifactsData : [],
  }));

  const { rerender } = render(
    <ReportPane runId="run-1" conversationId="conversation-1" conversationTitle="Thread" />,
  );

  expect(screen.getByText("Loading report")).toBeInTheDocument();
  expect(useArtifactsQueryMock.mock.calls[0]?.[1]).toMatchObject({ refetchInterval: 2500 });

  artifactsData = [buildArtifact()];
  rerender(<ReportPane runId="run-1" conversationId="conversation-1" conversationTitle="Thread" />);

  expect(await screen.findByTestId("report-document")).toHaveTextContent("Body copy");
});

test("persists local section edits per run across remounts", async () => {
  const user = userEvent.setup();

  const first = render(
    <ReportPane runId="run-1" conversationId="conversation-1" conversationTitle="Thread" />,
  );

  await user.click(await screen.findByRole("button", { name: "Edit" }));
  const textarea = screen.getByRole("textbox");
  await user.clear(textarea);
  await user.type(textarea, "Edited summary");
  await user.click(screen.getByRole("button", { name: "Save" }));

  expect(screen.getByTestId("report-document")).toHaveTextContent("Edited summary");

  first.unmount();

  render(<ReportPane runId="run-1" conversationId="conversation-1" conversationTitle="Thread" />);

  expect(await screen.findByTestId("report-document")).toHaveTextContent("Edited summary");
  expect(screen.queryByText("Body copy")).not.toBeInTheDocument();
});

test("clears the report snapshot for the active run", async () => {
  const user = userEvent.setup();

  render(<ReportPane runId="run-1" conversationId="conversation-1" conversationTitle="Thread" />);

  await user.click(await screen.findByRole("button", { name: "Clear" }));

  expect(screen.getByText("Report cleared")).toBeInTheDocument();
  expect(localStorage.getItem("researchlens:report-cleared:conversation-1:run-1")).toBe("1");
  expect(localStorage.getItem("researchlens:report-state:conversation-1:run-1")).toBeNull();
});

test("only marks the report pane as running while the run is active", () => {
  useRunQueryMock.mockImplementation((runId?: string) => ({
    data: runId ? { status: "running", display_status: "Running" } : undefined,
  }));
  useArtifactsQueryMock.mockImplementation((runId?: string) => ({
    data: runId ? [] : [],
  }));
  useArtifactTextQueryMock.mockImplementation(() => ({
    data: undefined,
    isLoading: false,
  }));

  const { rerender } = render(
    <ReportPane runId="run-1" conversationId="conversation-1" conversationTitle="Thread" />,
  );

  expect(document.querySelector("section.legacy-report-pane")).toHaveClass(
    "legacy-report-pane--running",
  );
  expect(screen.getByText("Progress card")).toBeInTheDocument();
  expect(screen.queryByText(/No report yet/i)).not.toBeInTheDocument();

  useRunQueryMock.mockImplementation((runId?: string) => ({
    data: runId ? { status: "succeeded", display_status: "Completed" } : undefined,
  }));

  rerender(<ReportPane runId="run-1" conversationId="conversation-1" conversationTitle="Thread" />);

  expect(document.querySelector("section.legacy-report-pane")).not.toHaveClass(
    "legacy-report-pane--running",
  );
  expect(screen.queryByText("Progress card")).not.toBeInTheDocument();
});
