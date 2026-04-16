import type { Components } from "react-markdown";

export const chatMarkdownComponents: Components = {
  h1: ({ children }) => (
    <h1 className="mb-1.5 text-base font-semibold text-slate-100">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="mb-1.5 text-sm font-semibold text-slate-100">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="mb-1.5 text-sm font-medium text-slate-100">{children}</h3>
  ),
  p: ({ children }) => (
    <p className="mb-1.5 leading-[1.5] last:mb-0">{children}</p>
  ),
  ul: ({ children }) => (
    <ul className="my-1.5 ml-5 list-disc space-y-1">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="my-1.5 ml-5 list-decimal space-y-1">{children}</ol>
  ),
  li: ({ children }) => (
    <li className="leading-[1.45] marker:text-slate-400 [&>p]:m-0 [&>p]:leading-[1.45] [&>ul]:mt-1 [&>ol]:mt-1">
      {children}
    </li>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-slate-100">{children}</strong>
  ),
  em: ({ children }) => <em className="italic text-slate-200">{children}</em>,
  code: (props) => {
    const inline =
      "inline" in props
        ? Boolean((props as { inline?: boolean }).inline)
        : false;
    const { children } = props;
    return inline ? (
      <code className="rounded bg-slate-900 px-1 py-0.5 font-mono text-xs text-emerald-200">
        {children}
      </code>
    ) : (
      <code className="font-mono">{children}</code>
    );
  },
  pre: ({ children }) => (
    <pre className="mt-2 overflow-auto rounded-md bg-slate-900 p-3 text-xs text-slate-200">
      {children}
    </pre>
  ),
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-emerald-300 underline underline-offset-2 hover:text-emerald-200"
    >
      {children}
    </a>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-slate-600 pl-3 italic text-slate-300/90">
      {children}
    </blockquote>
  ),
  hr: () => <hr className="my-3 border-slate-700" />,
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
