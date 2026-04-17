import type { Components } from "react-markdown";

export const chatMarkdownComponents: Components = {
  h1: ({ children }) => (
    <h1 className="chat-markdown__heading chat-markdown__heading--1">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="chat-markdown__heading chat-markdown__heading--2">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="chat-markdown__heading chat-markdown__heading--3">{children}</h3>
  ),
  p: ({ children }) => <p className="chat-markdown__paragraph">{children}</p>,
  ul: ({ children }) => <ul className="chat-markdown__list">{children}</ul>,
  ol: ({ children }) => (
    <ol className="chat-markdown__list chat-markdown__list--ordered">{children}</ol>
  ),
  li: ({ children }) => <li className="chat-markdown__list-item">{children}</li>,
  strong: ({ children }) => <strong className="chat-markdown__strong">{children}</strong>,
  em: ({ children }) => <em className="chat-markdown__emphasis">{children}</em>,
  code: (props) => {
    const inline =
      "inline" in props
        ? Boolean((props as { inline?: boolean }).inline)
        : false;
    const { children } = props;
    return inline ? (
      <code className="chat-markdown__code-inline">{children}</code>
    ) : (
      <code className="chat-markdown__code-block">{children}</code>
    );
  },
  pre: ({ children }) => <pre className="chat-markdown__pre">{children}</pre>,
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="chat-markdown__link"
    >
      {children}
    </a>
  ),
  blockquote: ({ children }) => (
    <blockquote className="chat-markdown__quote">{children}</blockquote>
  ),
  hr: () => <hr className="chat-markdown__rule" />,
};

export function normalizeChatMarkdown(input: string | null | undefined): string {
  if (!input) return "";
  return input
    .replace(/\r\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n");
}

export function formatActionLabel(actionId: string | null): string {
  if (!actionId) return "Action";
  if (actionId === "run_pipeline") return "Run research report";
  if (actionId === "quick_answer") return "Quick answer";
  return actionId.replace(/_/g, " ");
}
