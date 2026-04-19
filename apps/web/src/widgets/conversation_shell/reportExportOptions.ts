import type { ArtifactResponse } from "@researchlens/api-client";

export type ReportExportOptionId = "pdf" | "docx" | "md" | "html";

export type ReportExportOption = {
  id: ReportExportOptionId;
  label: string;
  description: string;
  artifact: ArtifactResponse | null;
};

const EXPORT_OPTION_META: Record<ReportExportOptionId, Omit<ReportExportOption, "artifact">> = {
  pdf: { id: "pdf", label: "PDF document", description: "Best for sharing and printing" },
  docx: { id: "docx", label: "Word document", description: "Editable in Microsoft Word" },
  md: { id: "md", label: "Markdown", description: "Plain text with formatting" },
  html: { id: "html", label: "HTML", description: "Web-ready format" },
};

function matchesFormat(artifact: ArtifactResponse, formatId: ReportExportOptionId) {
  const filename = artifact.filename.toLowerCase();
  const mediaType = artifact.media_type.toLowerCase();
  if (formatId === "pdf") return filename.endsWith(".pdf") || mediaType === "application/pdf";
  if (formatId === "docx")
    return filename.endsWith(".docx") || mediaType.includes("wordprocessingml");
  if (formatId === "md") return filename.endsWith(".md") || mediaType === "text/markdown";
  return filename.endsWith(".html") || mediaType === "text/html";
}

export function deriveReportExportOptions(artifacts: ArtifactResponse[]) {
  return (Object.keys(EXPORT_OPTION_META) as ReportExportOptionId[]).map((formatId) => ({
    ...EXPORT_OPTION_META[formatId],
    artifact: artifacts.find((artifact) => matchesFormat(artifact, formatId)) ?? null,
  }));
}
