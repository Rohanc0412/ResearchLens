import type { Components } from "react-markdown";

export const reportMarkdownComponents: Components = {
  h1: ({ children }) => (
    <h1 className="report-markdown__heading report-markdown__heading--1">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="report-markdown__heading report-markdown__heading--2">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="report-markdown__heading report-markdown__heading--3">{children}</h3>
  ),
  p: ({ children }) => <p className="report-markdown__paragraph">{children}</p>,
  ul: ({ children }) => <ul className="report-markdown__list">{children}</ul>,
  ol: ({ children }) => (
    <ol className="report-markdown__list report-markdown__list--ordered">{children}</ol>
  ),
  li: ({ children }) => <li className="report-markdown__list-item">{children}</li>,
  strong: ({ children }) => <strong className="report-markdown__strong">{children}</strong>,
  em: ({ children }) => <em className="report-markdown__emphasis">{children}</em>,
  code: (props) => {
    const inline =
      "inline" in props ? Boolean((props as { inline?: boolean }).inline) : false;
    const { children } = props;
    return inline ? (
      <code className="report-markdown__code-inline">{children}</code>
    ) : (
      <code className="report-markdown__code-block">{children}</code>
    );
  },
  pre: ({ children }) => <pre className="report-markdown__pre">{children}</pre>,
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="report-markdown__link"
    >
      {children}
    </a>
  ),
  blockquote: ({ children }) => (
    <blockquote className="report-markdown__quote">{children}</blockquote>
  ),
  hr: () => <hr className="report-markdown__rule" />,
};

export function normalizeReportMarkdown(input: string | null | undefined): string {
  if (!input) return "";
  return input.replace(/\r\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
}

export function extractReportTitle(markdown: string): string | null {
  const match = markdown.match(/^#\s+(.+)$/m);
  return match?.[1]?.trim() || null;
}

export function stripReportTitle(markdown: string): string {
  return markdown.replace(/^#\s+.+\n+/m, "").trim();
}
