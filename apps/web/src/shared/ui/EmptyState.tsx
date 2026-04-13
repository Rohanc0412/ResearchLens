import type { ReactNode } from "react";

export function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <section className="empty-state stack">
      <div className="eyebrow">Empty</div>
      <div>
        <h2 className="card__title">{title}</h2>
        <p className="page-subtitle">{body}</p>
      </div>
      {action}
    </section>
  );
}
