import { useState } from "react";
import { Outlet } from "react-router-dom";

import { ProjectSidebar } from "../../widgets/project_list/ProjectSidebar";

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="app-shell">
      <ProjectSidebar collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} />
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
