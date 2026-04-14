import type { MessageResponse } from "@researchlens/api-client";

import { formatDateTime } from "../../shared/lib/format";

function messageBody(message: MessageResponse) {
  if (message.content_text) return message.content_text;
  if (message.content_json) return JSON.stringify(message.content_json, null, 2);
  return "No message content.";
}

export function ChatMessageList({ messages }: { messages: MessageResponse[] }) {
  return (
    <section className="conversation-timeline" aria-label="Conversation messages">
      <div className="conversation-timeline__head">
        <div>
          <div className="eyebrow">Timeline</div>
          <strong>{messages.length} messages</strong>
        </div>
      </div>
      <div className="message-list">
        {messages.map((message) => (
          <article key={message.id} className="message" data-role={message.role}>
            <div className="message__meta">
              <span>{message.role}</span>
              <span>{formatDateTime(message.created_at)}</span>
            </div>
            <p>{messageBody(message)}</p>
          </article>
        ))}
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="eyebrow">Empty</div>
            <h2 className="card__title">No messages yet</h2>
            <p className="page-subtitle">Use the composer to add the first prompt or note.</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}
