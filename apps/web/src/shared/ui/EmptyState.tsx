import type { ReactNode } from "react";

export function EmptyState({
  icon = "empty",
  title,
  body,
  action,
}: {
  icon?: "empty" | "folder" | "message";
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <section className="empty-state stack">
      <span className="empty-state__icon" aria-hidden="true">
        {icon === "folder" ? (
          <svg viewBox="0 0 24 24">
            <path d="M3.75 7.75h6.5l1.55 2h8.45v7.5a2 2 0 0 1-2 2H5.75a2 2 0 0 1-2-2v-9.5Z" />
          </svg>
        ) : icon === "message" ? (
          <svg viewBox="0 0 24 24">
            <path d="M5.5 4.5h13a2 2 0 0 1 2 2v9.5a2 2 0 0 1-2 2H10l-4.5 2.5V18h0a2 2 0 0 1-2-2V6.5a2 2 0 0 1 2-2Z" />
          </svg>
        ) : null}
      </span>
      <div>
        <h2 className="card__title">{title}</h2>
        <p className="page-subtitle">{body}</p>
      </div>
      {action}
    </section>
  );
}
