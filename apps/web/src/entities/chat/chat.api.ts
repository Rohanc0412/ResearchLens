import {
  useMutation,
  useQuery,
  useQueryClient,
  type InfiniteData,
} from "@tanstack/react-query";

import { env } from "../../shared/config/env";
import { useAuth } from "../../app/providers/AuthProvider";
import type { ChatMessage, ChatSendResponse } from "./chat.types";

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const chatKeys = {
  messages: (conversationId: string) =>
    ["chat-messages", conversationId] as const,
};

// ---------------------------------------------------------------------------
// Message cache helpers
// ---------------------------------------------------------------------------

function mergeChatMessages(
  existing: ChatMessage[],
  additions: ChatMessage[],
): ChatMessage[] {
  const map = new Map<string, ChatMessage>();
  for (const m of existing) map.set(m.id, m);
  for (const m of additions) map.set(m.id, m);
  return Array.from(map.values()).sort((a, b) => {
    const byTime = a.created_at.localeCompare(b.created_at);
    return byTime !== 0 ? byTime : a.id.localeCompare(b.id);
  });
}

// ---------------------------------------------------------------------------
// Messages query (simple list, newest first)
// ---------------------------------------------------------------------------

export function useChatMessagesQuery(conversationId: string) {
  const auth = useAuth();

  return useQuery({
    queryKey: chatKeys.messages(conversationId),
    queryFn: async (): Promise<ChatMessage[]> => {
      const token = auth.accessToken;
      const response = await fetch(
        `${env.apiBaseUrl}/conversations/${encodeURIComponent(conversationId)}/messages`,
        {
          credentials: "include",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        },
      );
      if (!response.ok) throw new Error(`Failed to load messages (${response.status})`);
      const data = (await response.json()) as ChatMessage[];
      return data;
    },
    enabled: auth.status === "authenticated" && Boolean(conversationId),
  });
}

// ---------------------------------------------------------------------------
// Send message mutation (with SSE streaming)
// ---------------------------------------------------------------------------

type SendInput = {
  conversation_id: string;
  message: string;
  client_message_id: string;
  llm_model?: string | null;
  force_pipeline?: boolean;
};

export function useSendChatMessageMutation(
  conversationId: string,
  callbacks?: { onStatus?: () => void },
) {
  const auth = useAuth();
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (input: SendInput): Promise<ChatSendResponse> => {
      const token = auth.accessToken;
      const payload = {
        message: input.message,
        client_message_id: input.client_message_id,
        llm_model: input.llm_model,
        force_pipeline: input.force_pipeline ?? false,
      };
      const response = await fetch(
        `${env.apiBaseUrl}/conversations/${encodeURIComponent(conversationId)}/send`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify(payload),
        },
      );

      if (!response.ok) {
        const body = await response.text().catch(() => null);
        throw new Error(`Chat send failed (${response.status}): ${body ?? ""}`);
      }

      const contentType = response.headers.get("content-type") ?? "";

      if (contentType.includes("text/event-stream")) {
        return await parseSseResponse(response, callbacks);
      }

      return (await response.json()) as ChatSendResponse;
    },

    onMutate: async (input) => {
      const key = chatKeys.messages(conversationId);
      await qc.cancelQueries({ queryKey: key });
      const previous = qc.getQueryData<ChatMessage[]>(key);
      const optimisticId = `client:${input.client_message_id}`;
      const isAction = input.message.startsWith("__ACTION__:");
      const optimistic: ChatMessage = {
        id: optimisticId,
        role: "user",
        type: isAction ? "action" : "chat",
        content_text: input.message,
        content_json: null,
        created_at: new Date().toISOString(),
        client_message_id: input.client_message_id,
        optimistic: true,
      };
      qc.setQueryData<ChatMessage[]>(key, (prev) =>
        mergeChatMessages(prev ?? [], [optimistic]),
      );
      return { previous, optimisticId };
    },

    onError: (_err, _input, context) => {
      const key = chatKeys.messages(conversationId);
      if (context?.previous) {
        qc.setQueryData(key, context.previous);
      } else if (context?.optimisticId) {
        qc.setQueryData<ChatMessage[]>(key, (prev) =>
          (prev ?? []).filter((m) => m.id !== context.optimisticId),
        );
      }
    },

    onSuccess: (data, _input, context) => {
      const key = chatKeys.messages(conversationId);
      qc.setQueryData<ChatMessage[]>(key, (prev) => {
        const without = context?.optimisticId
          ? (prev ?? []).filter((m) => m.id !== context.optimisticId)
          : (prev ?? []);
        const additions = [data.user_message, data.assistant_message].filter(
          (m): m is ChatMessage => m != null,
        );
        return mergeChatMessages(without, additions.map((m) => ({ ...m, optimistic: false })));
      });
      void qc.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

// ---------------------------------------------------------------------------
// SSE parser
// ---------------------------------------------------------------------------

async function parseSseResponse(
  response: Response,
  callbacks?: { onStatus?: () => void },
): Promise<ChatSendResponse> {
  if (!response.body) throw new Error("SSE response body is missing");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let currentEvent = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          let data: unknown;
          try {
            data = JSON.parse(line.slice(6));
          } catch {
            continue;
          }
          if (currentEvent === "status") {
            callbacks?.onStatus?.();
          } else if (currentEvent === "answer") {
            return data as ChatSendResponse;
          }
        } else if (line === "") {
          currentEvent = "";
        }
      }
    }
  } finally {
    reader.cancel().catch(() => {});
  }
  throw new Error("SSE stream ended without answer event");
}
