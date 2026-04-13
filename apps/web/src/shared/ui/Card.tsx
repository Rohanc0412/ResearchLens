import type { PropsWithChildren, ReactNode } from "react";

import { cn } from "../lib/cn";

type CardProps = PropsWithChildren<{
  title?: ReactNode;
  meta?: ReactNode;
  actions?: ReactNode;
  className?: string;
  interactive?: boolean;
}>;

export function Card({
  title,
  meta,
  actions,
  className,
  interactive = false,
  children,
}: CardProps) {
  return (
    <section className={cn("card", interactive && "card--interactive", className)}>
      <div className="card__body">
        {title || actions ? (
          <header className="card__header">
            <div>
              {title ? <h2 className="card__title">{title}</h2> : null}
              {meta ? <div className="card__meta">{meta}</div> : null}
            </div>
            {actions}
          </header>
        ) : null}
        {children}
      </div>
    </section>
  );
}
