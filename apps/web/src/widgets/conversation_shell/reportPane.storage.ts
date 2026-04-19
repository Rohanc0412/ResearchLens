const REPORT_CLEAR_PREFIX = "researchlens:report-cleared";

function buildReportClearKey(conversationId: string, runId: string) {
  return `${REPORT_CLEAR_PREFIX}:${conversationId}:${runId}`;
}

export function isReportCleared(conversationId?: string, runId?: string | null) {
  if (!conversationId || !runId) return false;
  return localStorage.getItem(buildReportClearKey(conversationId, runId)) === "1";
}

export function setReportCleared(conversationId: string, runId: string) {
  localStorage.setItem(buildReportClearKey(conversationId, runId), "1");
}
