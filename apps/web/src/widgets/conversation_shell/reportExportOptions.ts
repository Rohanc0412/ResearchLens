export type ReportExportOptionId = "pdf" | "docx" | "md" | "html";

export type ReportExportOption = {
  id: ReportExportOptionId;
  label: string;
  description: string;
};

const EXPORT_OPTION_META: Record<ReportExportOptionId, ReportExportOption> = {
  pdf: { id: "pdf", label: "PDF document", description: "Best for sharing and printing" },
  docx: { id: "docx", label: "Word document", description: "Editable in Microsoft Word" },
  md: { id: "md", label: "Markdown", description: "Plain text with formatting" },
  html: { id: "html", label: "HTML", description: "Web-ready format" },
};

export function deriveReportExportOptions() {
  return Object.values(EXPORT_OPTION_META);
}
