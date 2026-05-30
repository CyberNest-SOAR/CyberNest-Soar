import { AppSidebar } from "./AppSidebar";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { User, LogOut, Bell } from "lucide-react";
import { Logo } from "./Logo";
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
    <div className="flex min-h-screen w-full bg-background relative overflow-hidden font-grotesk">
      {/* Background Aesthetics */}
      <div className="absolute inset-0 -z-10 pointer-events-none">
        <div className="absolute top-0 left-0 w-full h-full bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]" />
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px] -mr-64 -mt-64" />
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-accent/5 rounded-full blur-[120px] -ml-64 -mb-64" />
      </div>

      <AppSidebar userRole={userRole} />
      
      <SidebarInset className="flex flex-col min-w-0 bg-transparent">
        {/* Top Navigation */}
        <header className="h-16 border-b border-border/40 bg-background/60 backdrop-blur-xl flex items-center justify-between px-4 sm:px-6 sticky top-0 z-40">
          {/* Left: Sidebar Trigger */}
          <div className="flex items-center gap-3">
            <SidebarTrigger className="text-foreground hover:bg-accent/50 rounded-lg transition-colors p-2" />
            <div className="h-4 w-px bg-border/40 mx-2 hidden md:block" />
            <div className="hidden md:flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
              <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
              SYSTEM ACTIVE: {new Date().toLocaleDateString()}
            </div>
          </div>

          <div className="absolute left-1/2 -translate-x-1/2 hidden sm:flex items-center justify-center">
            <Logo size="md" />
          </div>

          {/* Right: Notification, ThemeToggle, User Menu */}
          <div className="flex items-center gap-1 sm:gap-3">
            <div className="hidden sm:flex items-center gap-1">
              <Button variant="ghost" size="icon" className="rounded-xl relative">
                <Bell className="h-4 w-4" />
                <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-background" />
              </Button>
            </div>
            
            <ThemeToggle />
            
            <div className="h-6 w-px bg-border/40 mx-1 hidden sm:block" />

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="flex items-center gap-2 h-10 px-1 sm:px-3 rounded-xl border border-border/40 bg-card/50 hover:bg-accent/50 transition-all group overflow-hidden"
                >
                  <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-lg group-hover:scale-105 transition-transform">
                    <User className="h-4 w-4 text-white" />
                  </div>
                  <div className="hidden sm:flex flex-col items-start leading-none gap-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider">
                      {userRole === "admin" ? "ADMINISTRATOR" : "ANALYST"}
                    </span>
                    <span className="text-[9px] text-muted-foreground font-mono">CN-0{userRole === "admin" ? "1" : "2"}</span>
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-64 glass p-2 border-border/40 shadow-2xl">
                <div className="px-3 py-4 flex flex-col gap-1">
                  <p className="text-sm font-bold">Security Operator</p>
                  <p className="text-[10px] text-muted-foreground font-mono">
                    AUTH_NODE: HQ-01-SEC
                  </p>
                  <div className="mt-3 flex items-center gap-2">
                    <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
                    <span className="text-[10px] uppercase font-bold text-green-500">Active Session</span>
                  </div>
                </div>
                <DropdownMenuSeparator className="bg-border/40" />
                <DropdownMenuItem
                  onClick={onLogout}
                  className="text-destructive cursor-pointer focus:text-destructive focus:bg-destructive/10 rounded-lg m-1 font-bold text-xs uppercase tracking-widest"
                >
                  <LogOut className="h-3.5 w-3.5 mr-2" />
                  Terminate Session
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Main Content Area */}
        <div className="flex-1 overflow-auto relative">
          <div className="w-full h-full p-4 sm:p-6 lg:p-8">
            {children}
          </div>
        </div>
      </SidebarInset>
    </div>
  );
};

export default AppLayout;
