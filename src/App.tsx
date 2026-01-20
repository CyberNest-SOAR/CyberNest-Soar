import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { SidebarProvider } from "@/components/ui/sidebar";
import { useAuth } from "./hooks/useAuth";

// Import pages
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ThreatIntelligence from "./pages/ThreatIntelligence";
import LogsDashboard from "./pages/LogsDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import MonitoringDashboard from "./pages/MonitoringDashboard";
import PlaybookConfig from "./pages/PlaybookConfig";
import Incidents from "./pages/Incidents";
import Reports from "./pages/Reports";


// Import layout components
import AppLayout from "./components/AppLayout";
import { ThemeProvider } from "./components/ThemeProvider";

const queryClient = new QueryClient();

const AppContent = () => {
  const { isAuthenticated, userRole, loading, signOut } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 border-4 border-cyber-blue/30 border-t-cyber-blue rounded-full animate-spin" />
          <p className="text-sm text-muted-foreground">Loading CyberNest-SOAR...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route 
        path="/login" 
        element={!isAuthenticated ? <Login /> : <Navigate to={userRole === "admin" ? "/admin-dashboard" : "/monitoring-dashboard"} replace />}
      />
      
      {isAuthenticated ? (
        <Route 
          path="/*" 
          element={
            <SidebarProvider defaultOpen={true}>
              <div className="min-h-screen flex w-full bg-background">
                <AppLayout onLogout={signOut} userRole={userRole}>
                  <Routes>
                    <Route 
                      path="/" 
                      element={<Navigate to={userRole === "admin" ? "/admin-dashboard" : "/monitoring-dashboard"} replace />} 
                    />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/threat-intelligence" element={<ThreatIntelligence />} />
                    <Route path="/logs" element={<LogsDashboard />} />
                    <Route path="/incidents" element={<Incidents />} />
                    <Route path="/reports" element={<Reports />} />
                    {userRole === "admin" ? (
                      <>
                        <Route path="/admin-dashboard" element={<AdminDashboard />} />
                        <Route path="/monitoring" element={<MonitoringDashboard />} />
                        <Route path="/playbooks" element={<PlaybookConfig />} />
                      </>
                    ) : (
                      <Route path="/monitoring-dashboard" element={<MonitoringDashboard />} />
                    )}
                    <Route 
                      path="*" 
                      element={<Navigate to={userRole === "admin" ? "/admin-dashboard" : "/monitoring-dashboard"} replace />} 
                    />
                  </Routes>
                </AppLayout>
              </div>
            </SidebarProvider>
          } 
        />
      ) : (
        <Route path="*" element={<Navigate to="/login" replace />} />
      )}
    </Routes>
  );
};

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark" storageKey="cybernest-theme">
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <AppContent />
          </BrowserRouter>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
