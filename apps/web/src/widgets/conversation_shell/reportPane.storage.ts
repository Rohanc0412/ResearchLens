import type { ReportDocument } from "./reportDocument";

const REPORT_CLEAR_PREFIX = "researchlens:report-cleared";
const REPORT_STATE_PREFIX = "researchlens:report-state";

function buildReportClearKey(conversationId: string, runId: string) {
  return `${REPORT_CLEAR_PREFIX}:${conversationId}:${runId}`;
}

function buildReportStateKey(conversationId: string, runId: string) {
  return `${REPORT_STATE_PREFIX}:${conversationId}:${runId}`;
}

export function isReportCleared(conversationId?: string, runId?: string | null) {
  if (!conversationId || !runId) return false;
  return localStorage.getItem(buildReportClearKey(conversationId, runId)) === "1";
}

export function setReportCleared(conversationId: string, runId: string) {
  localStorage.setItem(buildReportClearKey(conversationId, runId), "1");
}

function isReportDocument(value: unknown): value is ReportDocument {
  if (!value || typeof value !== "object") return false;
  const report = value as ReportDocument;
  if (typeof report.title !== "string" || !Array.isArray(report.sections)) return false;
  return report.sections.every((section) => {
    if (!section || typeof section !== "object") return false;
    if (typeof section.id !== "string" || typeof section.heading !== "string") return false;
    if (!Array.isArray(section.content)) return false;
    return section.content.every(
      (item) =>
        item &&
        typeof item === "object" &&
        typeof item.text === "string" &&
        (item.citations === undefined ||
          (Array.isArray(item.citations) &&
            item.citations.every((citation) => typeof citation === "number"))),
    );
  });
}

export function loadStoredReport(
  conversationId?: string,
  runId?: string | null,
): ReportDocument | null {
  if (!conversationId || !runId) return null;
  try {
    const raw = localStorage.getItem(buildReportStateKey(conversationId, runId));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as unknown;
    return isReportDocument(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export function persistStoredReport(
  conversationId: string,
  runId: string,
  report: ReportDocument,
) {
  const key = buildReportStateKey(conversationId, runId);
  if (report.sections.length === 0) {
    localStorage.removeItem(key);
    return;
  }
  localStorage.setItem(key, JSON.stringify(report));
}

export function clearStoredReport(conversationId: string, runId: string) {
  localStorage.removeItem(buildReportStateKey(conversationId, runId));
}
