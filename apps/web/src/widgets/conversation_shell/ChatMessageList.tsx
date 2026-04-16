import { type RefObject } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  chatMarkdownComponents,
  formatActionLabel,
  normalizeChatMarkdown,
} from "./chatMarkdown";
import { TypingIndicator } from "./TypingIndicator";
import type { ChatMessage, PipelineOfferAction } from "../../entities/chat/chat.types";

type ChatMessageListProps = {
  messages: ChatMessage[];
  isTyping: boolean;
  webSearching: boolean;
  isActionPending: boolean;
  activeRunId?: string | null;
  messagesEndRef: RefObject<HTMLDivElement>;
  onAction: (actionId: string) => void;
};

function displayMessageText(message: ChatMessage): string {
  if (message.type === "action") {
    const actionId =
      (message.content_json?.["action_id"] as string | undefined) ??
      (message.content_text ?? "").replace("__ACTION__:", "").trim();
    return formatActionLabel(actionId || null);
  }
  return message.content_text ?? "";
}

export function ChatMessageList({
  messages,
  isTyping,
  webSearching,
  isActionPending,
  activeRunId,
  messagesEndRef,
  onAction,
}: ChatMessageListProps) {
  return (
    <div
      className="flex-1 overflow-y-auto p-6"
      role="log"
      aria-live="polite"
      aria-label="Chat messages"
      aria-relevant="additions"
    >
      {messages.map((message) => {
        const isUser = message.role === "user";
        const isOffer = message.type === "pipeline_offer";
        const isRunStarted = message.type === "run_started";
        const isError = message.type === "error";
        const runId = isRunStarted
          ? (message.content_json?.["run_id"] as string | undefined)
          : undefined;
        const offer = message.content_json?.["offer"];
        const actions: PipelineOfferAction[] = Array.isArray(
          (offer as { actions?: unknown[] } | undefined)?.actions,
        )
          ? ((offer as { actions: PipelineOfferAction[] }).actions ?? [])
          : [];

        return (
          <div
            key={message.id}
            className={`mb-4 flex flex-col ${isUser ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-[90%] rounded-2xl px-4 py-3.5 text-sm leading-relaxed ${
                isUser || isError || message.type === "action"
                  ? "whitespace-pre-wrap"
                  : "whitespace-normal"
              } ${
                isUser
                  ? "rounded-br-sm border border-emerald-500/30 bg-emerald-500/15 text-slate-200"
                  : isError
                    ? "rounded-bl-sm border border-rose-500/40 bg-rose-500/10 text-rose-100"
                    : "rounded-bl-sm border border-slate-800 bg-slate-900 text-slate-200"
              }`}
            >
              {message.type === "action" ? (
                <span>{displayMessageText(message)}</span>
              ) : (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={chatMarkdownComponents}
                >
                  {normalizeChatMarkdown(message.content_text)}
                </ReactMarkdown>
              )}

              {isRunStarted && runId && activeRunId !== runId ? (
                <div className="mt-2 text-xs text-slate-400">
                  Run queued — open the research panel to track progress.
                </div>
              ) : null}
            </div>

            {isOffer && actions.length > 0 ? (
              <div className="mt-2 flex flex-wrap gap-2">
                {actions.map((action) => (
                  <button
                    key={action.id ?? action.label}
                    onClick={() => {
                      if (!action.id) return;
                      onAction(action.id);
                    }}
                    disabled={isActionPending}
                    className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs text-emerald-200 transition-colors hover:border-emerald-500/60 hover:bg-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {action.label ?? formatActionLabel(action.id ?? null)}
                  </button>
                ))}
              </div>
            ) : null}

            <div className="mt-1.5 font-mono text-xs text-slate-500">
              {new Date(message.created_at).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: false,
              })}
            </div>
          </div>
        );
      })}

      {isTyping ? (
        <div className="inline-block rounded-2xl rounded-bl-sm border border-slate-800 bg-slate-900 px-4 py-3.5">
          {webSearching ? (
            <span className="text-sm text-slate-400">Searching the web…</span>
          ) : (
            <TypingIndicator />
          )}
        </div>
      ) : null}

      <div ref={messagesEndRef} />
    </div>
  );
}
