import type { ReactNode } from "react";

export function ErrorBanner({
  title = "Something went wrong",
  body,
  action,
}: {
  title?: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <section className="error-banner stack" role="alert">
      <div className="eyebrow">Error</div>
      <div>
        <h2 className="card__title">{title}</h2>
        <p className="page-subtitle">{body}</p>
      </div>
      {action}
    </section>
  );
}
