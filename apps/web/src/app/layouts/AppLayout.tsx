import { Outlet } from "react-router-dom";

import { ProjectSidebar } from "../../widgets/project_list/ProjectSidebar";

export function AppLayout() {
  return (
    <div className="app-shell">
      <ProjectSidebar />
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
