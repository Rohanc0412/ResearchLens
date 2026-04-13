import type { PropsWithChildren, ReactNode } from "react";
import { motion, useReducedMotion } from "framer-motion";

export function Page({
  title,
  eyebrow,
  subtitle,
  actions,
  children,
}: PropsWithChildren<{
  title: string;
  eyebrow: string;
  subtitle?: string;
  actions?: ReactNode;
}>) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.div
      className="page-shell"
      initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <header className="page-header">
        <div>
          <div className="eyebrow">{eyebrow}</div>
          <h1 className="display-heading page-title">{title}</h1>
          {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
        </div>
        {actions}
      </header>
      {children}
    </motion.div>
  );
}
