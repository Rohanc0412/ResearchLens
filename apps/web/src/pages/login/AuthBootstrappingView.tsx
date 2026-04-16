import { motion, useReducedMotion } from "framer-motion";

import { Spinner } from "../../shared/ui/Spinner";
import { AuthOverviewPanel } from "./authScreenContent";

export function AuthBootstrappingView() {
  const shouldReduceMotion = useReducedMotion();
  return (
    <div className="auth-shell">
      <AuthOverviewPanel />
      <main className="auth-workspace">
        <motion.section
          className="auth-card auth-card--status"
          initial={shouldReduceMotion ? false : { opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.24, ease: "easeOut" }}
          aria-label="Restoring session"
        >
          <span className="auth-status-orb" aria-hidden="true">
            <Spinner />
          </span>
          <div className="auth-card__heading">
            <span className="auth-card__eyebrow">Session restore</span>
            <h2>Restoring your workspace session</h2>
            <p>
              ResearchLens is checking for a valid refresh-backed session before showing the
              sign-in form.
            </p>
          </div>
          <div className="auth-support-card">
            <strong>Why this happens</strong>
            <p>
              Access tokens are held in memory. On load, the app attempts a refresh-cookie
              restore so returning users can continue without a duplicate login.
            </p>
          </div>
        </motion.section>
      </main>
    </div>
  );
}
