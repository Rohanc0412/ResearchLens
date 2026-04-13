import { useRouteError } from "react-router-dom";

import { ErrorBanner } from "../../shared/ui/ErrorBanner";

export function RouteErrorView() {
  const error = useRouteError();

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <ErrorBanner
          title="Route failed to load"
          body={error instanceof Error ? error.message : "Unexpected route error."}
        />
      </div>
    </div>
  );
}
