import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../../app/providers/AuthProvider";
import { useConversationsQuery } from "../../entities/conversation/conversation.api";
import { useProjectsQuery } from "../../entities/project/project.api";
import { cn } from "../../shared/lib/cn";
import { SidebarActionButton, SidebarLinkItem } from "./SidebarEntry";

const shieldIcon = (
  <>
    <path d="M12 3.75 18.25 6v5.1c0 4.1-2.55 7.8-6.25 9.15-3.7-1.35-6.25-5.05-6.25-9.15V6L12 3.75Z" />
    <path d="m9.7 11.9 1.45 1.45 3.25-3.55" />
  </>
);
const newProjectIcon = (
  <>
    <path d="M5 12h14" />
    <path d="M12 5v14" />
  </>
);
const projectIcon = <path d="M3.75 7.75h6.5l1.55 2h8.45v7.5a2 2 0 0 1-2 2H5.75a2 2 0 0 1-2-2v-9.5Z" />;
const conversationIcon = (
  <>
    <path d="M6 7.5h12" />
    <path d="M6 12h7" />
    <path d="M5.5 4.5h13a2 2 0 0 1 2 2v9.5a2 2 0 0 1-2 2H10l-4.5 2.5V18a2 2 0 0 1-2-2V6.5a2 2 0 0 1 2-2Z" />
  </>
);
const logoutIcon = (
  <>
    <path d="M9 5H5.75a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2H9" />
    <path d="M13 8.5 16.5 12 13 15.5" />
    <path d="M16.25 12H8" />
  </>
);

function SidebarBrand({
  collapsed,
  onCollapse,
  onExpand,
}: {
  collapsed: boolean;
  onCollapse: () => void;
  onExpand: () => void;
}) {
  return (
    <div className={cn("app-sidebar__brand", collapsed && "is-collapsed")}>
      {collapsed ? (
        <button
          aria-label="Expand sidebar"
          className="app-sidebar__brand-toggle"
          onClick={onExpand}
          title="Expand sidebar"
          type="button"
        >
          <svg className="app-sidebar__brand-shield" viewBox="0 0 24 24" aria-hidden="true">
            {shieldIcon}
          </svg>
          <svg className="app-sidebar__brand-open" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M8 5h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" />
            <path d="m10 9.5 2.5 2.5L10 14.5" />
          </svg>
        </button>
      ) : (
        <>
          <div className="app-sidebar__brand-main">
            <span className="app-sidebar__mark" aria-hidden="true">
              <svg viewBox="0 0 24 24">{shieldIcon}</svg>
            </span>
            <span className="app-sidebar__title">ResearchLens</span>
          </div>
          <button aria-label="Collapse sidebar" className="app-sidebar__collapse" onClick={onCollapse} title="Collapse sidebar" type="button">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M8 5h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" />
              <path d="M14 9.5 11.5 12l2.5 2.5" />
            </svg>
          </button>
        </>
      )}
    </div>
  );
}

function SidebarProjects({
  collapsed,
  loading,
  hasError,
  onCreateProject,
  projects,
}: {
  collapsed: boolean;
  hasError: boolean;
  loading: boolean;
  onCreateProject: () => void;
  projects: Array<{ id: string; name: string }>;
}) {
  return (
    <>
      {!collapsed ? <section className="app-sidebar__section"><div className="eyebrow">Workspace</div></section> : null}
      <SidebarActionButton collapsed={collapsed} icon={newProjectIcon} onClick={onCreateProject} title={collapsed ? "New project" : undefined}>
        <span>New project</span>
      </SidebarActionButton>
      <div className="sidebar-list">
        {loading ? <span className={cn("sidebar-empty", collapsed && "is-collapsed")}>Loading...</span> : null}
        {hasError ? <span className={cn("sidebar-empty", "is-error", collapsed && "is-collapsed")}>Failed</span> : null}
        {!loading && !hasError && projects.length === 0 ? <span className={cn("sidebar-empty", collapsed && "is-collapsed")}>No projects</span> : null}
        {projects.map((project) => (
          <SidebarLinkItem key={project.id} collapsed={collapsed} icon={projectIcon} title={collapsed ? project.name : undefined} to={`/projects/${project.id}`}>
            <span className="sidebar-item__content">
              <strong>{project.name}</strong>
            </span>
          </SidebarLinkItem>
        ))}
      </div>
    </>
  );
}

function SidebarConversations({
  conversations,
  currentProjectId,
}: {
  conversations: Array<{ id: string; last_message_at: string | null; title: string }>;
  currentProjectId: string | null;
}) {
  if (!currentProjectId) {
    return null;
  }

  return (
    <section className="app-sidebar__section">
      <div className="eyebrow">Recent Conversations</div>
      <div className="sidebar-list">
        {conversations.map((conversation) => (
          <SidebarLinkItem key={conversation.id} collapsed={false} icon={conversationIcon} to={`/projects/${currentProjectId}/conversations/${conversation.id}`}>
            <span className="sidebar-item__content">
              <strong>{conversation.title}</strong>
              <span className="meta-line">
                {conversation.last_message_at ? `Active ${new Date(conversation.last_message_at).toLocaleString()}` : "No messages yet"}
              </span>
            </span>
          </SidebarLinkItem>
        ))}
      </div>
    </section>
  );
}

function SidebarAccount({
  collapsed,
  onLogout,
}: {
  collapsed: boolean;
  onLogout: () => void;
}) {
  return (
    <div className="app-sidebar__account">
      {!collapsed ? <div className="eyebrow">Account</div> : null}
      <SidebarLinkItem collapsed={collapsed} icon={shieldIcon} title={collapsed ? "Security" : undefined} to="/security">
        <span className="sidebar-item__content">
          <span>Security</span>
        </span>
      </SidebarLinkItem>
      <SidebarActionButton collapsed={collapsed} icon={logoutIcon} onClick={onLogout} title={collapsed ? "Logout" : undefined}>
        <span>Logout</span>
      </SidebarActionButton>
    </div>
  );
}

export function ProjectSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const auth = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const projectMatch = location.pathname.match(/^\/projects\/([^/]+)/);
  const currentProjectId = projectMatch?.[1] ? decodeURIComponent(projectMatch[1]) : null;
  const projects = useProjectsQuery();
  const conversations = useConversationsQuery(currentProjectId ?? "");
  const projectItems = projects.data ?? [];
  const recentConversations = (conversations.data ?? []).slice(0, 6);

  return (
    <aside className={cn("app-sidebar", collapsed && "is-collapsed")}>
      <SidebarBrand collapsed={collapsed} onCollapse={() => setCollapsed(true)} onExpand={() => setCollapsed(false)} />
      <nav className="app-sidebar__nav">
        <div className="app-sidebar__scroll">
          <SidebarProjects
            collapsed={collapsed}
            hasError={projects.isError}
            loading={projects.isLoading}
            onCreateProject={() => navigate("/projects?new=1")}
            projects={projectItems}
          />
          {!collapsed ? <SidebarConversations conversations={recentConversations} currentProjectId={currentProjectId} /> : null}
        </div>
        <SidebarAccount collapsed={collapsed} onLogout={() => void auth.logout()} />
      </nav>
      <div className="app-sidebar__footer">
        {!collapsed ? <span className="app-sidebar__version">v0.1</span> : null}
      </div>
    </aside>
  );
}
