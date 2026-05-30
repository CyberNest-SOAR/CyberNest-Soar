import { useState, useEffect } from "react";
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
  Mail,
  Globe,
  Cpu,
  Database,
  SlidersHorizontal,
  Activity,
  ChevronDown,
  ChevronRight
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
import { motion, AnimatePresence } from "framer-motion";

interface MenuItem {
  title: string;
  url: string;
  icon: any;
  roles?: UserRole[];
}

interface MenuCategory {
  title: string;
  icon: any;
  items: MenuItem[];
  roles?: UserRole[];
}

const categories: MenuCategory[] = [
  {
    title: "SOC",
    icon: Shield,
    items: [
      { title: "Command Center", url: "/soc/command-center", icon: BarChart3 },
      { title: "Alerts Center", url: "/soc/alerts-center", icon: Terminal },
      { title: "Alerts Table", url: "/soc/alerts-table", icon: Database },
      { title: "Incident Response", url: "/soc/incident-response", icon: AlertTriangle },
    ]
  },
  {
    title: "Assets",
    icon: Monitor,
    items: [
      { title: "Asset Intelligence", url: "/assets/asset-intelligence", icon: Search },
      { title: "Endpoint Health", url: "/assets/endpoint-health", icon: Monitor },
      { title: "IT Hygiene", url: "/assets/it-hygiene", icon: Shield },
    ]
  },
  {
    title: "Intel",
    icon: Globe,
    items: [
      { title: "Phishing Center", url: "/intel/phishing-center", icon: Mail },
      { title: "Threat Intel Center", url: "/intel/threat-intel-center", icon: Globe },
    ]
  },
  {
    title: "Automation",
    icon: Workflow,
    items: [
      { title: "Playbook Config", url: "/automation/playbooks-config", icon: Workflow, roles: ["admin"] },
      { title: "Playbooks & Automation", url: "/automation/playbooks-automation", icon: SlidersHorizontal },
    ]
  },
  {
    title: "AI",
    icon: Cpu,
    items: [
      { title: "AI Operations", url: "/ai/ai-operations", icon: Cpu },
    ]
  },
  {
    title: "Admin",
    icon: Users,
    roles: ["admin"],
    items: [
      { title: "System Dashboard", url: "/admin/dashboard", icon: Users },
      { title: "Admin Health", url: "/admin/admin-health", icon: Activity },
      { title: "Reporting & Audit", url: "/admin/reporting-audit", icon: FileText },
    ]
  }
];

interface AppSidebarProps {
  userRole: UserRole;
}

export function AppSidebar({ userRole }: AppSidebarProps) {
  const { open: sidebarOpen } = useSidebar();
  const location = useLocation();
  const currentPath = location.pathname;

  // Track expanded categories
  const [expanded, setExpanded] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = { "SOC": true };
    categories.forEach(cat => {
      if (cat.items.some(item => item.url === currentPath)) {
        initial[cat.title] = true;
      }
    });
    return initial;
  });

  // Toggle category expansion
  const toggleCategory = (title: string) => {
    setExpanded(prev => ({
      ...prev,
      [title]: !prev[title]
    }));
  };

  // Sync expanded categories when path changes
  useEffect(() => {
    categories.forEach(cat => {
      if (cat.items.some(item => item.url === currentPath)) {
        setExpanded(prev => ({ ...prev, [cat.title]: true }));
      }
    });
  }, [currentPath]);

  // Filter categories by user role
  const filteredCategories = categories
    .filter(cat => !cat.roles || cat.roles.includes(userRole))
    .map(cat => ({
      ...cat,
      items: cat.items.filter(item => !item.roles || item.roles.includes(userRole))
    }))
    .filter(cat => cat.items.length > 0);

  return (
    <Sidebar className="border-r border-border/40 bg-sidebar/85 backdrop-blur-xl">
      <SidebarContent className="flex flex-col h-full overflow-hidden select-none">
        
        {/* Logo Section */}
        <div className="flex items-center justify-center h-24 border-b border-border/40 px-6 shrink-0 bg-card/10">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
          >
            <Logo size={sidebarOpen ? "md" : "sm"} showText={sidebarOpen} />
          </motion.div>
        </div>

        {/* Scrollable Navigation Items */}
        <div className="flex-1 overflow-y-auto pr-1 pl-1 py-6 custom-scrollbar space-y-4">
          {filteredCategories.map((category, i) => {
            const isExpanded = expanded[category.title] && sidebarOpen;
            const CategoryIcon = category.icon;
            const isChildActive = category.items.some(item => item.url === currentPath);

            return (
              <div key={category.title} className="space-y-1">
                {/* Category Header */}
                <button
                  onClick={() => toggleCategory(category.title)}
                  className={`w-full flex items-center justify-between px-4 py-2.5 rounded-xl transition-all duration-300 group
                    ${
                      isChildActive 
                        ? "bg-primary/5 text-primary border border-primary/10 shadow-[0_0_15px_rgba(59,130,246,0.05)]" 
                        : "text-muted-foreground hover:bg-muted/20 hover:text-foreground border border-transparent"
                    }`}
                >
                  <div className="flex items-center gap-3.5">
                    <CategoryIcon className={`h-4 w-4 shrink-0 transition-transform duration-300 group-hover:scale-110 ${isChildActive ? "text-primary" : "text-muted-foreground"}`} />
                    {sidebarOpen && (
                      <span className="text-[10px] font-black uppercase tracking-[0.2em] font-sans">
                        {category.title}
                      </span>
                    )}
                  </div>
                  {sidebarOpen && (
                    <div>
                      {isExpanded ? (
                        <ChevronDown className="h-3.5 w-3.5 text-muted-foreground/60 transition-transform duration-300" />
                      ) : (
                        <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/60 transition-transform duration-300" />
                      )}
                    </div>
                  )}
                </button>

                {/* Collapsible Submenu */}
                <AnimatePresence initial={false}>
                  {isExpanded && (
                    <motion.div
                      key={`${category.title}-submenu`}
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25, ease: "easeInOut" }}
                      className="overflow-hidden"
                    >
                      <div className="pl-4 mt-1 flex flex-col gap-1 border-l border-border/30 ml-6">
                        {category.items.map((item, itemIdx) => {
                          const isActive = currentPath === item.url;
                          const ItemIcon = item.icon;

                          return (
                            <NavLink
                              key={item.url}
                              to={item.url}
                              className={
                                `flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-300 group relative text-xs
                                 ${
                                   isActive
                                     ? "bg-primary/10 text-primary font-bold shadow-[inset_0_0_8px_rgba(59,130,246,0.1)] border border-primary/25"
                                     : "text-muted-foreground/80 hover:bg-muted/15 hover:text-foreground border border-transparent"
                                 }`
                              }
                            >
                              <ItemIcon className={`h-3.5 w-3.5 shrink-0 transition-all ${isActive ? "text-primary text-glow-primary" : "text-muted-foreground/50 group-hover:text-foreground"}`} />
                              <span className="font-semibold tracking-wider font-mono">{item.title}</span>
                              {isActive && (
                                <motion.div 
                                  layoutId="active-indicator"
                                  className="absolute right-0 w-1.5 h-3.5 bg-primary rounded-l-full shadow-[0_0_10px_rgba(99,102,241,0.8)]"
                                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                />
                              )}
                            </NavLink>
                          );
                        })}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>

        {/* Status Section / Footer */}
        {sidebarOpen && (
          <div className="p-6 border-t border-border/40 shrink-0 bg-card/10 space-y-4">
            <div className="p-4 rounded-xl bg-card/40 border border-border/40 space-y-3 glass">
              <div className="flex justify-between items-center text-[9px] font-black uppercase tracking-widest text-muted-foreground/60">
                <span>SOC Telemetry</span>
                <span className="text-emerald-500 flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_6px_rgba(16,185,129,0.5)]" />
                  Synced
                </span>
              </div>
              <div className="h-1 w-full bg-muted/40 rounded-full overflow-hidden">
                <motion.div 
                  animate={{ width: ["30%", "75%", "45%", "100%", "55%"] }}
                  transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
                  className="h-full bg-gradient-to-r from-primary to-accent" 
                />
              </div>
            </div>
            <div className="text-[8px] font-mono text-muted-foreground/35 text-center uppercase tracking-[0.3em]">
              SOAR CORE // v4.2.0-PRO
            </div>
          </div>
        )}
      </SidebarContent>
    </Sidebar>
  );
}

