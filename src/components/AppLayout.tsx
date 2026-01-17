import { AppSidebar } from "./AppSidebar";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { User, LogOut } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { UserRole } from "@/hooks/useAuth";

interface AppLayoutProps {
  children: React.ReactNode;
  onLogout: () => void;
  userRole: UserRole;
}

const AppLayout = ({ children, onLogout, userRole }: AppLayoutProps) => {
  return (
    <>
      <AppSidebar userRole={userRole} />
      <div className="flex-1 flex flex-col">
        {/* Top Navigation */}
        <header className="h-16 border-b border-border bg-card flex items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-2 sm:gap-4">
            <SidebarTrigger className="text-foreground hover:bg-muted" />
            <h1 className="text-lg sm:text-xl font-grotesk font-semibold text-cyber-blue">
              SOAR Dashboard
            </h1>
          </div>
          
          <div className="flex items-center gap-2 sm:gap-4">
            <div className="hidden sm:block text-sm text-muted-foreground">
              Security Operations Center
            </div>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  <span>Admin</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={onLogout} className="text-destructive cursor-pointer">
                  <LogOut className="h-4 w-4 mr-2" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 p-4 sm:p-6 bg-background overflow-auto">
          {children}
        </main>
      </div>
    </>
  );
};

export default AppLayout;