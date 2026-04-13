import type { PropsWithChildren, ReactNode } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

type DialogProps = PropsWithChildren<{
  open: boolean;
  title: ReactNode;
  description?: ReactNode;
  onClose: () => void;
}>;

export function Dialog({
  open,
  title,
  description,
  onClose,
  children,
}: DialogProps) {
  const reduceMotion = useReducedMotion();

  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          className="app-dialog__backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.section
            aria-modal="true"
            className="app-dialog__panel stack"
            role="dialog"
            onClick={(event) => event.stopPropagation()}
            initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 18, scale: 0.98 }}
            animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0, scale: 1 }}
            exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 12, scale: 0.98 }}
            transition={{ duration: 0.18 }}
          >
            <header className="stack">
              <div className="eyebrow">Dialog</div>
              <div>
                <h2 className="card__title">{title}</h2>
                {description ? <p className="page-subtitle">{description}</p> : null}
              </div>
            </header>
            {children}
          </motion.section>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
