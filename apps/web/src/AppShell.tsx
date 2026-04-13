import { RouterProvider } from "react-router-dom";

import { AppProviders } from "./app/providers/AppProviders";
import { appRouter } from "./app/routes/router";

export function AppShell() {
  return (
    <AppProviders>
      <RouterProvider router={appRouter} />
    </AppProviders>
  );
}
