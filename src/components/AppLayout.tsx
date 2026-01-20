import { AppSidebar } from "./AppSidebar";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { User, LogOut, Bell } from "lucide-react";
import Logo from "../logts-nobg.png";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ThemeToggle } from "./ThemeToggle";
import { UserRole } from "@/hooks/useAuth";
import { Badge } from "@/components/ui/badge";

interface AppLayoutProps {
  children: React.ReactNode;
  onLogout: () => void;
  userRole: UserRole;
}

const AppLayout = ({ children, onLogout, userRole }: AppLayoutProps) => {
  return (
    <>
      <AppSidebar userRole={userRole} />
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Navigation */}
        <header className="h-16 border-b border-border bg-card/80 backdrop-blur-sm flex items-center justify-between px-4 sm:px-6 sticky top-0 z-40 relative">

          {/* Left: Sidebar Trigger */}
          <div className="flex items-center gap-3">
            <SidebarTrigger className="text-foreground hover:bg-accent/50 rounded-lg transition-colors" />
          </div>

          {/* Center: Logo + Title */}
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center gap-2">
            <img src={Logo} alt="Logo" className="h-12 w-auto" />
            <span className="font-bold text-lg text-gray-900 dark:text-white">
              CyberNest-SOAR
            </span>
          </div>


          {/* Right: Badge, ThemeToggle, User Menu */}
          <div className="flex items-center gap-2 sm:gap-3">

            <ThemeToggle />

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="flex items-center gap-2 h-9 px-3 rounded-lg border border-border/50 bg-background/50 hover:bg-accent/50 transition-all"
                >
                  <div className="h-6 w-6 rounded-full bg-gradient-to-br from-cyber-blue to-cyber-green flex items-center justify-center">
                    <User className="h-3.5 w-3.5 text-white" />
                  </div>
                  <span className="hidden sm:inline text-sm font-medium">
                    {userRole === "admin" ? "Admin" : "Analyst"}
                  </span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-popover border-border">
                <div className="px-2 py-1.5">
                  <p className="text-sm font-medium">Security Operator</p>
                  <p className="text-xs text-muted-foreground">
                    {userRole === "admin" ? "Administrator" : "SOC Analyst"}
                  </p>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={onLogout}
                  className="text-destructive cursor-pointer focus:text-destructive focus:bg-destructive/10"
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 p-4 sm:p-6 bg-background overflow-auto">
          <div className="max-w-[1800px] mx-auto animate-fade-in">{children}</div>
        </main>
      </div>
    </>
  );
};

export default AppLayout;
