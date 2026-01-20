import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  Shield,
  Terminal,
  Users,
  Workflow,
  AlertTriangle,
  FileText,
  BarChart3,
  Monitor,
  Search,
} from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import Logo from "../logts-nobg.png";
import { UserRole } from "@/hooks/useAuth";

const adminMenuItems = [
  { title: "Admin Dashboard", url: "/admin-dashboard", icon: Users },
  { title: "Dashboard", url: "/dashboard", icon: BarChart3 },
  { title: "Monitoring", url: "/monitoring", icon: Monitor },
  { title: "Threat Intelligence", url: "/threat-intelligence", icon: Search },
  { title: "Logs Dashboard", url: "/logs", icon: Terminal },
  { title: "Playbook Config", url: "/playbooks", icon: Workflow },
  { title: "Incidents", url: "/incidents", icon: AlertTriangle },
  { title: "Reports", url: "/reports", icon: FileText },
];

const analystMenuItems = [
  { title: "Monitoring", url: "/monitoring-dashboard", icon: Monitor },
  { title: "Dashboard", url: "/dashboard", icon: BarChart3 },
  { title: "Threat Intelligence", url: "/threat-intelligence", icon: Search },
  { title: "Logs Dashboard", url: "/logs", icon: Terminal },
  { title: "Incidents", url: "/incidents", icon: AlertTriangle },
  { title: "Reports", url: "/reports", icon: FileText },
];

interface AppSidebarProps {
  userRole: UserRole;
}

export function AppSidebar({ userRole }: AppSidebarProps) {
  const { open: sidebarOpen } = useSidebar();
  const location = useLocation();
  const currentPath = location.pathname;

  const isActive = (path: string) => currentPath === path;

  const menuItems = userRole === "admin" ? adminMenuItems : analystMenuItems;

  return (
    <Sidebar className="bg-sidebar">
      <SidebarContent className="bg-sidebar">
        {/* Logo Section */}
        <div className="flex items-center gap-2 p-4">
          <img src={Logo} alt="Logo" className="h-12 w-auto" />
          <span className="text-sidebar-foreground font-bold text-lg">
            CyberNest-SOAR
          </span>
        </div>

        <SidebarGroup className="mt-4">
          <SidebarGroupLabel className="text-sidebar-foreground/60 uppercase tracking-wider text-[10px] font-semibold px-4 mb-2">
            Security Modules
          </SidebarGroupLabel>
          <SidebarGroupContent>
           <SidebarMenu className="space-y-3 px-2"> {/* space-y-3 for spacing between items */}
  {menuItems.map((item) => (
    <SidebarMenuItem key={item.title}>
      <SidebarMenuButton asChild className="p-0">
        <NavLink
          to={item.url}
          className={({ isActive: navIsActive }) =>
            `flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-300 group 
             ${
               navIsActive || isActive(item.url)
                 ? "bg-gradient-to-r from-blue-500/20 to-blue-500/10 text-blue-500 shadow-lg"
                 : "text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 hover:text-blue-500 dark:hover:text-blue-400"
             }`
          }
        >
          <item.icon
            className={`h-5 w-5 shrink-0 transition-transform duration-300 group-hover:scale-110`}
          />
          <span className="font-medium text-sm truncate">{item.title}</span>
        </NavLink>
      </SidebarMenuButton>
    </SidebarMenuItem>
  ))}
</SidebarMenu>


          </SidebarGroupContent>
        </SidebarGroup>

        {/* Version info */}
        <div className="mt-auto p-4 border-t border-sidebar-border">
          <div className="text-[10px] text-sidebar-foreground/40 text-center">
            CyberNest-SOAR v1.0.0
          </div>
        </div>
      </SidebarContent>
    </Sidebar>

  );
}
