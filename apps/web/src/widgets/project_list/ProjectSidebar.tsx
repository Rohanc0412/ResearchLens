import { motion, useReducedMotion } from "framer-motion";
import { NavLink, useParams } from "react-router-dom";

import { useAuth } from "../../app/providers/AuthProvider";
import { useConversationsQuery } from "../../entities/conversation/conversation.api";
import { useProjectsQuery } from "../../entities/project/project.api";
import { cn } from "../../shared/lib/cn";
import { Button } from "../../shared/ui/Button";

export function ProjectSidebar({
  collapsed,
  onToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
}) {
  const reduceMotion = useReducedMotion();
  const auth = useAuth();
  const params = useParams();
  const currentProjectId = params.projectId;
  const projects = useProjectsQuery();
  const conversations = useConversationsQuery(currentProjectId ?? "");

  return (
    <motion.aside
      animate={reduceMotion ? undefined : { width: collapsed ? 88 : 320 }}
      className="app-sidebar"
      transition={{ duration: 0.18, ease: "easeOut" }}
    >
      <div className="app-sidebar__brand">
        <div className="app-sidebar__eyebrow">ResearchLens</div>
        {!collapsed ? (
          <>
            <div className="app-sidebar__title">Research Console</div>
            <div className="meta-line">{auth.user?.email ?? "Session restoring"}</div>
          </>
        ) : null}
      </div>

      <div className="row row--between">
        <Button compact variant="ghost" onClick={onToggle}>
          {collapsed ? "Expand" : "Collapse"}
        </Button>
        {!collapsed ? (
          <Button compact variant="ghost" onClick={() => void auth.logout()}>
            Logout
          </Button>
        ) : null}
      </div>

      <div className="app-sidebar__scroll">
        <section className="app-sidebar__section">
          {!collapsed ? <div className="eyebrow">Projects</div> : null}
          <div className="sidebar-list">
            {(projects.data ?? []).map((project) => (
              <NavLink key={project.id} className="sidebar-item" to={`/projects/${project.id}`}>
                {({ isActive }) => (
                  <div className={cn("sidebar-item__inner", isActive && "is-active")}>
                    <span className="sidebar-item__glyph">{project.name.slice(0, 1)}</span>
                    {!collapsed ? (
                      <span>
                        <strong>{project.name}</strong>
                        {!collapsed ? (
                          <span className="meta-line">
                            {project.description ?? "No project description yet"}
                          </span>
                        ) : null}
                      </span>
                    ) : null}
                  </div>
                )}
              </NavLink>
            ))}
          </div>
        </section>

        {!collapsed && currentProjectId ? (
          <section className="app-sidebar__section">
            <div className="eyebrow">Recent Conversations</div>
            <div className="sidebar-list">
              {(conversations.data ?? []).slice(0, 6).map((conversation) => (
                <NavLink
                  key={conversation.id}
                  className="sidebar-item sidebar-item--conversation"
                  to={`/projects/${currentProjectId}/conversations/${conversation.id}`}
                >
                  {({ isActive }) => (
                    <div className={cn("sidebar-item__inner", isActive && "is-active")}>
                      <span className="sidebar-item__glyph">C</span>
                      <span>
                        <strong>{conversation.title}</strong>
                        <span className="meta-line">
                          {conversation.last_message_at
                            ? `Active ${new Date(conversation.last_message_at).toLocaleString()}`
                            : "No messages yet"}
                        </span>
                      </span>
                    </div>
                  )}
                </NavLink>
              ))}
            </div>
          </section>
        ) : null}

        {!collapsed ? (
          <section className="app-sidebar__section">
            <NavLink to="/security">
              <Button compact variant="ghost">
                Security
              </Button>
            </NavLink>
          </section>
        ) : null}
      </div>
    </motion.aside>
  );
}
