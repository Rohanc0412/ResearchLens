import type { PropsWithChildren, ReactNode } from "react";
import { motion, useReducedMotion } from "framer-motion";

import { cn } from "../lib/cn";

export function Page({
  title,
  eyebrow,
  subtitle,
  actions,
  centered = false,
  children,
}: PropsWithChildren<{
  title: string;
  eyebrow: string;
  subtitle?: string;
  actions?: ReactNode;
  centered?: boolean;
}>) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.div
      className={cn("page-shell", centered && "page-shell--centered")}
      initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <header className="page-header">
        <div>
          {eyebrow ? <div className="eyebrow">{eyebrow}</div> : null}
          <h1 className="display-heading page-title">{title}</h1>
          {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
        </div>
        {actions}
      </header>
      {children}
    </motion.div>
  );
}
