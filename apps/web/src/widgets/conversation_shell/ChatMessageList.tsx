import { type RefObject } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { chatMarkdownComponents, formatActionLabel, normalizeChatMarkdown } from "./chatMarkdown";
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
      className="legacy-chat-timeline"
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
            className={`legacy-chat-message ${
              isUser ? "legacy-chat-message--user" : "legacy-chat-message--assistant"
            } ${isError ? "legacy-chat-message--error" : ""}`}
          >
            <div className="legacy-chat-message__bubble">
              {message.type === "action" ? (
                <span className="legacy-chat-message__action-text">
                  {displayMessageText(message)}
                </span>
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={chatMarkdownComponents}>
                  {normalizeChatMarkdown(message.content_text)}
                </ReactMarkdown>
              )}

              {isRunStarted && runId && activeRunId !== runId ? (
                <div className="legacy-chat-message__status-note">
                  Tracking progress in the research report panel.
                </div>
              ) : null}
            </div>

            {isOffer && actions.length > 0 ? (
              <div className="legacy-chat-message__actions">
                {actions.map((action) => (
                  <button
                    key={action.id ?? action.label}
                    onClick={() => {
                      if (!action.id) return;
                      onAction(action.id);
                    }}
                    disabled={isActionPending}
                    className="legacy-chat-message__action"
                  >
                    {action.label ?? formatActionLabel(action.id ?? null)}
                  </button>
                ))}
              </div>
            ) : null}

            <div className="legacy-chat-message__meta">
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
        <div className="legacy-chat-message legacy-chat-message--assistant">
          <div className="legacy-chat-message__bubble">
            {webSearching ? (
              <span className="legacy-chat-message__status-note">Searching the web...</span>
            ) : (
              <TypingIndicator />
            )}
          </div>
        </div>
      ) : null}

      <div ref={messagesEndRef} />
    </div>
  );
}
