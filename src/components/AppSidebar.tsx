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
import { Logo } from "@/components/Logo";
import { UserRole } from "@/hooks/useAuth";

const adminMenuItems = [
  { title: "Team Monitoring", url: "/admin-dashboard", icon: Users },
  { title: "Threat Analysis Dashboard", url: "/dashboard", icon: BarChart3 },
  { title: "Monitoring", url: "/monitoring", icon: Monitor },
  { title: "Phishing Detection Center", url: "/threat-intelligence", icon: Search },
  { title: "Alert Center", url: "/logs", icon: Terminal },
  { title: "Playbook Config", url: "/playbooks", icon: Workflow },
  { title: "Incidents", url: "/incidents", icon: AlertTriangle },
  { title: "Reports", url: "/reports", icon: FileText },
];

const analystMenuItems = [
  { title: "Monitoring", url: "/monitoring-dashboard", icon: Monitor },
  { title: "Dashboard", url: "/dashboard", icon: BarChart3 },
  { title: "Phishing Detection Center", url: "/threat-intelligence", icon: Search },
  { title: "Alert Center", url: "/logs", icon: Terminal },
  { title: "Incidents", url: "/incidents", icon: AlertTriangle },
  { title: "Reports", url: "/reports", icon: FileText },
];

interface AppSidebarProps {
  userRole: UserRole;
}

import { motion } from "framer-motion";

export function AppSidebar({ userRole }: AppSidebarProps) {
  const { open: sidebarOpen } = useSidebar();
  const location = useLocation();
  const currentPath = location.pathname;

  const menuItems = userRole === "admin" ? adminMenuItems : analystMenuItems;

  return (
    <Sidebar className="border-r border-border bg-sidebar">
      <SidebarContent>
        {/* Logo Section */}
        <div className="flex items-center justify-start h-20 border-b border-border/50 px-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <Logo size="sm" />
          </motion.div>
        </div>

        <SidebarGroup className="px-4 mt-8">
          <SidebarGroupLabel className="text-[10px] font-black uppercase tracking-[0.3em] text-muted-foreground/40 px-4 mb-6">
            Main Interface
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-1">
              {menuItems.map((item, i) => (
                <motion.div
                  key={item.title}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <NavLink
                        to={item.url}
                        className={({ isActive }) =>
                          `flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 group relative
                           ${
                             isActive
                               ? "bg-primary/10 text-primary"
                               : "text-muted-foreground hover:bg-muted/30 hover:text-foreground"
                           }`
                        }
                      >
                        <item.icon className={`h-5 w-5 shrink-0 transition-all ${currentPath === item.url ? "text-primary" : "text-muted-foreground group-hover:text-foreground"}`} />
                        <span className="font-bold text-xs uppercase tracking-widest">{item.title}</span>
                        {currentPath === item.url && (
                          <motion.div 
                            layoutId="active-indicator"
                            className="absolute right-0 w-1 h-5 bg-primary rounded-l-full shadow-[0_0_10px_rgba(99,102,241,0.8)]"
                          />
                        )}
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </motion.div>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Status section */}
        <div className="mt-auto p-8 space-y-6">
          <div className="p-5 rounded-2xl bg-card border border-border/40 space-y-4">
            <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-widest text-muted-foreground/60">
              <span>Security Node</span>
              <span className="text-primary">Online</span>
            </div>
            <div className="h-1 w-full bg-muted rounded-full overflow-hidden">
              <motion.div 
                animate={{ width: ["20%", "80%", "50%", "100%", "60%"] }}
                transition={{ duration: 15, repeat: Infinity }}
                className="h-full bg-primary" 
              />
            </div>
          </div>
          <div className="text-[9px] font-mono text-muted-foreground/30 text-center uppercase tracking-[0.4em]">
            v4.2.0-PRO
          </div>
        </div>
      </SidebarContent>
    </Sidebar>
  );
}
