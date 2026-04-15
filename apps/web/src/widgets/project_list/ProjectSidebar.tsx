import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";
import { NavLink, useNavigate, useParams } from "react-router-dom";

import { useAuth } from "../../app/providers/AuthProvider";
import { useConversationsQuery } from "../../entities/conversation/conversation.api";
import { useProjectsQuery } from "../../entities/project/project.api";
import { cn } from "../../shared/lib/cn";

function Icon({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span className={cn("sidebar-icon", className)} aria-hidden="true">
      <svg viewBox="0 0 24 24">{children}</svg>
    </span>
  );
}

export function ProjectSidebar({
  collapsed,
  onToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
}) {
  const reduceMotion = useReducedMotion();
  const auth = useAuth();
  const navigate = useNavigate();
  const params = useParams();
  const currentProjectId = params.projectId;
  const projects = useProjectsQuery();
  const conversations = useConversationsQuery(currentProjectId ?? "");

  return (
    <motion.aside
      animate={reduceMotion ? undefined : { width: collapsed ? 76 : 280 }}
      className="app-sidebar"
      transition={{ duration: 0.18, ease: "easeOut" }}
    >
      <div className="app-sidebar__brand row row--between">
        <div className="app-sidebar__brand-main">
          <span className="app-sidebar__mark" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M12 3.75 18.25 6v5.1c0 4.1-2.55 7.8-6.25 9.15-3.7-1.35-6.25-5.05-6.25-9.15V6L12 3.75Z" />
              <path d="m9.7 11.9 1.45 1.45 3.25-3.55" />
            </svg>
          </span>
          {!collapsed ? <span className="app-sidebar__title">ResearchLens</span> : null}
        </div>
        <button
          className="app-sidebar__collapse"
          type="button"
          onClick={onToggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M8 5h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" />
            <path d={collapsed ? "m10 9.5 2.5 2.5L10 14.5" : "M14 9.5 11.5 12l2.5 2.5"} />
          </svg>
        </button>
      </div>

      {!collapsed ? (
        <section className="app-sidebar__section">
          <div className="eyebrow">Workspace</div>
          <button
            className="sidebar-item__inner sidebar-action"
            type="button"
            onClick={() => navigate("/projects")}
          >
            <Icon>
              <path d="M5 12h14" />
              <path d="M12 5v14" />
            </Icon>
            <span>New project</span>
          </button>

          <div className="sidebar-list">
            {(projects.data ?? []).length === 0 ? (
              <span className="sidebar-empty">No projects</span>
            ) : (
              (projects.data ?? []).map((project) => (
                <NavLink key={project.id} className="sidebar-item" to={`/projects/${project.id}`}>
                  {({ isActive }) => (
                    <div className={cn("sidebar-item__inner", isActive && "is-active")}>
                      <Icon>
                        <path d="M3.75 7.75h6.5l1.55 2h8.45v7.5a2 2 0 0 1-2 2H5.75a2 2 0 0 1-2-2v-9.5Z" />
                      </Icon>
                      <span>
                        <strong>{project.name}</strong>
                      </span>
                    </div>
                  )}
                </NavLink>
              ))
            )}
          </div>
        </section>
      ) : null}

      <div className="app-sidebar__scroll">
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
                      <Icon>
                        <path d="M6 7.5h12" />
                        <path d="M6 12h7" />
                        <path d="M5.5 4.5h13a2 2 0 0 1 2 2v9.5a2 2 0 0 1-2 2H10l-4.5 2.5V18h0a2 2 0 0 1-2-2V6.5a2 2 0 0 1 2-2Z" />
                      </Icon>
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
      </div>

      {!collapsed ? (
        <div className="app-sidebar__account">
          <div className="eyebrow">Account</div>
          <NavLink className="sidebar-item" to="/security">
            {({ isActive }) => (
              <div className={cn("sidebar-item__inner", isActive && "is-active")}>
                <Icon>
                  <path d="M12 3.75 18.25 6v5.1c0 4.1-2.55 7.8-6.25 9.15-3.7-1.35-6.25-5.05-6.25-9.15V6L12 3.75Z" />
                </Icon>
                <span>Security</span>
              </div>
            )}
          </NavLink>
          <button className="sidebar-item__inner sidebar-action" type="button" onClick={() => void auth.logout()}>
            <Icon>
              <path d="M9 5H5.75a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2H9" />
              <path d="M13 8.5 16.5 12 13 15.5" />
              <path d="M16.25 12H8" />
            </Icon>
            <span>Logout</span>
          </button>
          <span className="app-sidebar__version">v0.1</span>
        </div>
      ) : null}
    </motion.aside>
  );
}
