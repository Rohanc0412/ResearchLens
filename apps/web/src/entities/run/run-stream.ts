import type { RunEventResponse } from "@researchlens/api-client";

import { env } from "../../shared/config/env";

type StreamCallbacks = {
  accessToken: string | null;
  getRefreshedAccessToken: () => Promise<string | null>;
  onEvent: (event: RunEventResponse) => void;
  onConnectionChange?: (connected: boolean) => void;
  onError?: (error: Error) => void;
  signal: AbortSignal;
  runId: string;
  startAfterEventId?: number;
};

const terminalStatuses = new Set(["succeeded", "failed", "canceled"]);

export function parseSseChunk(chunk: string) {
  const lines = chunk.split("\n");
  let eventType = "message";
  let id = "";
  const data: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventType = line.slice(6).trim();
    } else if (line.startsWith("id:")) {
      id = line.slice(3).trim();
    } else if (line.startsWith("data:")) {
      data.push(line.slice(5).trim());
    }
  }

  if (!id || data.length === 0) {
    return null;
  }

  return {
    id: Number(id),
    eventType,
    payload: JSON.parse(data.join("\n")) as RunEventResponse,
  };
}

async function connectSse({
  accessToken,
  runId,
  lastEventId,
  signal,
}: {
  accessToken: string | null;
  runId: string;
  lastEventId?: number;
  signal: AbortSignal;
}) {
  return fetch(`${env.apiBaseUrl}/runs/${runId}/events`, {
    method: "GET",
    signal,
    credentials: "include",
    headers: {
      Accept: "text/event-stream",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...(lastEventId ? { "Last-Event-ID": String(lastEventId) } : {}),
    },
  });
}

export async function streamRunEvents({
  accessToken,
  getRefreshedAccessToken,
  onEvent,
  onConnectionChange,
  onError,
  signal,
  runId,
  startAfterEventId,
}: StreamCallbacks) {
  let lastEventId = startAfterEventId;
  let token = accessToken;
  let terminalSeen = false;

  while (!signal.aborted) {
    const response = await connectSse({
      accessToken: token,
      runId,
      lastEventId,
      signal,
    });

    if (response.status === 401) {
      token = await getRefreshedAccessToken();
      if (!token) {
        throw new Error("Session expired while streaming run progress.");
      }
      continue;
    }

    if (!response.ok || !response.body) {
      throw new Error(`Run stream failed with status ${response.status}.`);
    }

    onConnectionChange?.(true);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (!signal.aborted) {
        const result = await reader.read();
        if (result.done) {
          break;
        }
        buffer += decoder.decode(result.value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          if (!part.trim() || part.startsWith(":")) {
            continue;
          }

          const parsed = parseSseChunk(part);
          if (!parsed) {
            continue;
          }

          lastEventId = parsed.id;
          terminalSeen = terminalStatuses.has(parsed.payload.status);
          onEvent(parsed.payload);
        }
      }
    } finally {
      onConnectionChange?.(false);
      reader.releaseLock();
    }

    if (terminalSeen || signal.aborted) {
      return;
    }

    onError?.(new Error("Run stream disconnected. Reconnecting..."));
    await new Promise((resolve) => window.setTimeout(resolve, 1000));
  }
}
