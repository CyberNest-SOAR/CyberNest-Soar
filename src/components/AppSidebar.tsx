import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  Shield,
  Mail,
  Network,
  Lock,
  Terminal,
  Users,
  Workflow,
  AlertTriangle,
  FileText,
  BarChart3,
  Monitor,
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
import { UserRole } from "@/hooks/useAuth";

const adminMenuItems = [
  { title: "Admin Dashboard", url: "/admin-dashboard", icon: Users },
  { title: "Dashboard", url: "/dashboard", icon: BarChart3 },
  { title: "Monitoring", url: "/monitoring", icon: Monitor },
  { title: "Phishing Emails", url: "/phishing", icon: Mail },
  { title: "DDoS Attacks", url: "/ddos", icon: Network },
  { title: "Brute Force", url: "/brute-force", icon: Lock },
  { title: "Logs Dashboard", url: "/logs", icon: Terminal },
  { title: "Playbook Config", url: "/playbooks", icon: Workflow },
  { title: "Incidents", url: "/incidents", icon: AlertTriangle },
  { title: "Reports", url: "/reports", icon: FileText },
];

const analystMenuItems = [
  { title: "Monitoring Dashboard", url: "/monitoring-dashboard", icon: Monitor },
  { title: "Dashboard", url: "/dashboard", icon: BarChart3 },
  { title: "Phishing Emails", url: "/phishing", icon: Mail },
  { title: "DDoS Attacks", url: "/ddos", icon: Network },
  { title: "Brute Force", url: "/brute-force", icon: Lock },
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
    <Sidebar className="border-r border-sidebar-border">
      <SidebarContent className="bg-sidebar">
        <div className="p-4 border-b border-sidebar-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-cyber flex items-center justify-center">
              <Shield className="h-5 w-5 text-white" />
            </div>
          
              <div className="min-w-0">
                <h2 className="font-grotesk font-bold text-sidebar-foreground truncate">SecureOps</h2>
                <p className="text-xs text-sidebar-foreground/70 truncate">Security Analytics</p>
              </div>
            
          </div>
        </div>

        <SidebarGroup className="mt-4">
          <SidebarGroupLabel className="text-sidebar-foreground/70 uppercase tracking-wide text-xs font-medium px-4">
            Security Modules
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton 
                    asChild 
                    className="mx-2"
                  >
                     <NavLink
                      to={item.url}
                      className={({ isActive: navIsActive }) =>
                        `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                          navIsActive || isActive(item.url)
                            ? "bg-sidebar-accent text-sidebar-primary border border-sidebar-primary/20 cyber-glow"
                            : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
                        }`
                      }
                    >
                      <item.icon className="h-5 w-5 shrink-0" />
                    
                        <span className="font-medium truncate">{item.title}</span>
                      
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}