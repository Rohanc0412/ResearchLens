import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import { ArtifactsPage } from "./ArtifactsPage";

const useRunQueryMock = vi.fn();
const useArtifactsQueryMock = vi.fn();
const useArtifactTextQueryMock = vi.fn();
const useRunEvidenceSummaryQueryMock = vi.fn();
const useSectionEvidenceQueryMock = vi.fn();
const useEvaluationSummaryQueryMock = vi.fn();
const useEvaluationIssuesQueryMock = vi.fn();
const useRepairSummaryQueryMock = vi.fn();
const mutateAsyncMock = vi.fn();

vi.mock("../../entities/run/run.api", () => ({
  useRunQuery: (runId: string) => useRunQueryMock(runId),
}));

vi.mock("../../entities/artifact/artifact.api", () => ({
  useArtifactsQuery: (...args: unknown[]) => useArtifactsQueryMock(...args),
  useArtifactTextQuery: (...args: unknown[]) => useArtifactTextQueryMock(...args),
  useArtifactDownloadMutation: () => ({ mutateAsync: mutateAsyncMock }),
}));

vi.mock("../../entities/evidence/evidence.api", () => ({
  useRunEvidenceSummaryQuery: (...args: unknown[]) => useRunEvidenceSummaryQueryMock(...args),
  useSectionEvidenceQuery: (...args: unknown[]) => useSectionEvidenceQueryMock(...args),
  useEvaluationSummaryQuery: (...args: unknown[]) => useEvaluationSummaryQueryMock(...args),
  useEvaluationIssuesQuery: (...args: unknown[]) => useEvaluationIssuesQueryMock(...args),
  useRepairSummaryQuery: (...args: unknown[]) => useRepairSummaryQueryMock(...args),
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
    byte_size: 2048,
    sha256: "hash",
    created_at: "2026-04-19T15:00:00Z",
    manifest_id: null,
    ...overrides,
  };
}

function buildRunEvidenceSummary() {
  return {
    run_id: "run-1",
    project_id: "project-1",
    conversation_id: "conversation-1",
    section_count: 1,
    source_count: 1,
    chunk_count: 1,
    claim_count: 1,
    issue_count: 1,
    repaired_section_count: 0,
    unresolved_section_count: 1,
    latest_evaluation_pass_id: "eval-1",
    latest_repair_pass_id: "repair-1",
    artifact_count: 2,
    sections: [
      {
        section_id: "sec-1",
        title: "Findings",
        section_order: 0,
        repaired: false,
        issue_count: 1,
      },
    ],
  };
}

function buildSectionTrace() {
  return {
    section_id: "sec-1",
    section_title: "Findings",
    section_order: 0,
    canonical_text: "Full canonical text",
    canonical_summary: "Section summary",
    repaired: false,
    latest_evaluation_result_id: "eval-result-1",
    repair_result_id: "repair-result-1",
    claims: [],
    issues: [
      {
        issue_id: "trace-issue-1",
        issue_type: "unsupported_claim",
        severity: "high",
        verdict: "unsupported",
        message: "Evidence mismatch",
        rationale: "The claim is not grounded in evidence.",
        repair_hint: "Revise this claim",
      },
    ],
    evidence_chunks: [
      {
        chunk_id: "chunk-1",
        source_id: "source-1",
        source_title: "Primary source",
        chunk_index: 2,
        excerpt_text: "Evidence excerpt",
      },
    ],
    source_refs: [
      {
        source_id: "source-1",
        canonical_key: "source:key:1",
        title: "Primary source",
        identifiers: {},
      },
    ],
    unresolved_quality_findings: [
      {
        issue_id: "finding-1",
        issue_type: "unsupported_claim",
        severity: "high",
        verdict: "unsupported",
        message: "Open finding",
        rationale: "Still unresolved",
        repair_hint: "Check the citation",
      },
    ],
  };
}

function renderPage(path = "/runs/run-1/artifacts") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/runs/:runId/artifacts" element={<ArtifactsPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  mutateAsyncMock.mockReset();
  mutateAsyncMock.mockResolvedValue({
    blob: new Blob(["download body"]),
    filename: "report.md",
  });
  HTMLAnchorElement.prototype.click = vi.fn();
  URL.createObjectURL = vi.fn(() => "blob:test");
  URL.revokeObjectURL = vi.fn();

  useRunQueryMock.mockImplementation(() => ({
    data: {
      status: "succeeded",
      current_stage: "export",
      display_status: "Completed",
      display_stage: "Export",
      updated_at: "2026-04-19T15:05:00Z",
    },
  }));

  useArtifactsQueryMock.mockImplementation(() => ({
    data: [
      buildArtifact(),
      buildArtifact({
        id: "artifact-pdf",
        filename: "report.pdf",
        media_type: "application/pdf",
        kind: "report_pdf",
      }),
    ],
    isLoading: false,
  }));

  useArtifactTextQueryMock.mockImplementation((artifactId?: string) => ({
    data:
      artifactId === "artifact-md"
        ? {
            filename: "report.md",
            mediaType: "text/markdown",
            text: "# Report\n\nAlpha copy",
          }
        : undefined,
    isLoading: false,
  }));

  useRunEvidenceSummaryQueryMock.mockImplementation(() => ({
    data: buildRunEvidenceSummary(),
    isLoading: false,
  }));

  useSectionEvidenceQueryMock.mockImplementation((_runId?: string, sectionId?: string) => ({
    data: sectionId === "sec-1" ? buildSectionTrace() : undefined,
    isLoading: false,
  }));

  useEvaluationSummaryQueryMock.mockImplementation(() => ({
    data: {
      evaluation_pass_id: "eval-1",
      section_count: 1,
      evaluated_section_count: 1,
      issue_count: 1,
      sections_requiring_repair_count: 1,
      quality_pct: 96,
      unsupported_claim_rate: 10,
      pass_rate: 80,
      ragas_faithfulness_pct: 88,
      issues_by_type: { unsupported_claim: 1 },
      repair_recommended: true,
      sections_requiring_repair: ["sec-1"],
    },
    isLoading: false,
  }));

  useEvaluationIssuesQueryMock.mockImplementation(() => ({
    data: [
      {
        issue_id: "issue-1",
        run_id: "run-1",
        evaluation_pass_id: "eval-1",
        section_id: "sec-1",
        section_title: "Findings",
        section_order: 0,
        claim_id: null,
        claim_index: null,
        claim_text: null,
        verdict: null,
        issue_type: "unsupported_claim",
        severity: "high",
        message: "Claim is unsupported",
        rationale: "No supporting evidence was found.",
        cited_chunk_ids: [],
        supported_chunk_ids: [],
        allowed_chunk_ids: [],
        repair_hint: "Add evidence",
        created_at: "2026-04-19T15:10:00Z",
      },
    ],
    isLoading: false,
  }));

  useRepairSummaryQueryMock.mockImplementation(() => ({
    data: {
      repair_pass_id: "repair-1",
      run_id: "run-1",
      status: "completed",
      selected_count: 1,
      changed_count: 1,
      unresolved_count: 0,
      sections: [
        {
          section_id: "sec-1",
          section_title: "Findings",
          section_order: 0,
          status: "completed",
          action: "rewrite",
          changed: true,
          evaluation_section_result_id: "result-1",
          repair_result_id: "repair-result-1",
          reevaluation_pass_id: null,
          unresolved_reason: null,
        },
      ],
    },
    isLoading: false,
  }));
});

test("defaults to the artifacts tab", () => {
  renderPage();

  expect(screen.getByRole("tab", { name: "Artifacts" })).toHaveAttribute("aria-selected", "true");
  expect(screen.getByText("Artifact library")).toBeInTheDocument();
});

test("selects the evidence tab and section from query params", () => {
  renderPage("/runs/run-1/artifacts?tab=evidence&section=sec-1");

  expect(screen.getByRole("tab", { name: "Evidence" })).toHaveAttribute("aria-selected", "true");
  expect(screen.getByText("Section summary")).toBeInTheDocument();
  expect(screen.getByText("Evidence excerpt")).toBeInTheDocument();
});

test("renders the selected artifact preview from the focus param", () => {
  renderPage("/runs/run-1/artifacts?focus=artifact-md");

  expect(screen.getByText("Alpha copy")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "report.md" })).toBeInTheDocument();
});

test("downloads an artifact without clearing the current preview", async () => {
  const user = userEvent.setup();

  renderPage("/runs/run-1/artifacts?focus=artifact-md");

  await user.click(screen.getByRole("button", { name: "Download report.md" }));

  await waitFor(() => expect(mutateAsyncMock).toHaveBeenCalledWith(buildArtifact()));
  expect(screen.getByText("Alpha copy")).toBeInTheDocument();
});

test("renders the evaluation tab with summary, issues, and repair data", () => {
  renderPage("/runs/run-1/artifacts?tab=evaluation");

  expect(screen.getByRole("tab", { name: "Evaluation" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  expect(screen.getByText("96.0%")).toBeInTheDocument();
  expect(screen.getByText("Claim is unsupported")).toBeInTheDocument();
  expect(screen.getByText("Findings")).toBeInTheDocument();
});

test("shows the artifact empty state", () => {
  useArtifactsQueryMock.mockImplementation(() => ({
    data: [],
    isLoading: false,
  }));

  renderPage();

  expect(screen.getByText("No artifacts yet")).toBeInTheDocument();
});

test("shows the evidence error state", () => {
  useRunEvidenceSummaryQueryMock.mockImplementation(() => ({
    data: undefined,
    isLoading: false,
    error: new Error("failed"),
  }));

  renderPage("/runs/run-1/artifacts?tab=evidence");

  expect(screen.getByText("Evidence summary could not be loaded.")).toBeInTheDocument();
});

test("shows the evaluation empty state when no summary exists", () => {
  useEvaluationSummaryQueryMock.mockImplementation(() => ({
    data: null,
    isLoading: false,
  }));
  useEvaluationIssuesQueryMock.mockImplementation(() => ({
    data: [],
    isLoading: false,
  }));
  useRepairSummaryQueryMock.mockImplementation(() => ({
    data: null,
    isLoading: false,
  }));

  renderPage("/runs/run-1/artifacts?tab=evaluation");

  expect(screen.getByText("No evaluation summary yet")).toBeInTheDocument();
});
