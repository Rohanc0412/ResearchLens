import { Navigate, Outlet, useLocation } from "react-router-dom";

import { Spinner } from "../../shared/ui/Spinner";
import { useAuth } from "../providers/AuthProvider";

export function ProtectedRoute() {
  const auth = useAuth();
  const location = useLocation();

  if (auth.status === "bootstrapping") {
    return (
      <div className="auth-shell">
        <Spinner />
      </div>
    );
  }

  if (auth.status !== "authenticated") {
    return <Navigate to="/login" replace state={{ next: location.pathname }} />;
  }

  return <Outlet />;
}
