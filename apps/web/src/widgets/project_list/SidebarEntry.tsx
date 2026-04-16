import type { ReactNode } from "react";
import { NavLink, type To } from "react-router-dom";

import { cn } from "../../shared/lib/cn";

function SidebarBody({
  active,
  children,
  collapsed,
  icon,
}: {
  active?: boolean;
  children?: ReactNode;
  collapsed: boolean;
  icon: ReactNode;
}) {
  return (
    <span className={cn("sidebar-item__inner", collapsed && "is-collapsed", active && "is-active")}>
      {active && !collapsed ? <span className="sidebar-item__rail" aria-hidden="true" /> : null}
      <span className="sidebar-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24">{icon}</svg>
      </span>
      {!collapsed ? children : null}
    </span>
  );
}

export function SidebarLinkItem({
  children,
  collapsed,
  icon,
  title,
  to,
}: {
  children?: ReactNode;
  collapsed: boolean;
  icon: ReactNode;
  title?: string;
  to: To;
}) {
  return (
    <NavLink className="sidebar-item" title={title} to={to}>
      {({ isActive }) => (
        <SidebarBody active={isActive} collapsed={collapsed} icon={icon}>
          {children}
        </SidebarBody>
      )}
    </NavLink>
  );
}

export function SidebarActionButton({
  children,
  collapsed,
  icon,
  onClick,
  title,
}: {
  children?: ReactNode;
  collapsed: boolean;
  icon: ReactNode;
  onClick: () => void;
  title?: string;
}) {
  return (
    <button className={cn("sidebar-action", collapsed && "is-collapsed")} onClick={onClick} title={title} type="button">
      <SidebarBody collapsed={collapsed} icon={icon}>
        {children}
      </SidebarBody>
    </button>
  );
}
