import { Navigate, Outlet, useLocation } from "react-router-dom";

import { Spinner } from "../../shared/ui/Spinner";
import { useAuth } from "../providers/AuthProvider";

export function ProtectedRoute() {
  const auth = useAuth();
  const location = useLocation();

  if (auth.status === "bootstrapping") {
    return (
      <div className="auth-shell">
        <main className="auth-workspace auth-workspace--centered">
          <section className="auth-card auth-card--status" aria-label="Restoring session">
            <span className="auth-status-orb" aria-hidden="true">
              <Spinner />
            </span>
            <div className="auth-card__heading">
              <span className="auth-card__eyebrow">Session restore</span>
              <h2>Restoring your workspace session</h2>
              <p>Checking for a valid refresh-backed session before routing into the app.</p>
            </div>
          </section>
        </main>
      </div>
    );
  }

  if (auth.status !== "authenticated") {
    return (
      <Navigate
        to="/login"
        replace
        state={{ next: `${location.pathname}${location.search}${location.hash}` }}
      />
    );
  }

  return <Outlet />;
}
