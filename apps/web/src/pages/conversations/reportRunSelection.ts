import type { ChatMessage } from "../../entities/chat/chat.types";

function normalizeRunId(value: string | null | undefined) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

export function extractLatestRunId(messages: ChatMessage[]) {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];
    if (message?.type !== "run_started") continue;
    const runId = message.content_json?.["run_id"];
    if (typeof runId === "string" && runId.trim()) return runId;
  }
  return null;
}

export function resolveReportRunId({
  urlRunId,
  messages,
  conversationId,
}: {
  urlRunId?: string | null;
  messages: ChatMessage[];
  conversationId: string;
}) {
  return (
    normalizeRunId(urlRunId) ??
    extractLatestRunId(messages) ??
    normalizeRunId(localStorage.getItem(`researchlens:last-run:${conversationId}`))
  );
}
