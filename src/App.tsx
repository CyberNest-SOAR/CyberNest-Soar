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
import PhishingEmails from "./pages/PhishingEmails";
import DDoSAttacks from "./pages/DDoSAttacks";
import BruteForce from "./pages/BruteForce";
import LogsDashboard from "./pages/LogsDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import MonitoringDashboard from "./pages/MonitoringDashboard";
import PlaybookConfig from "./pages/PlaybookConfig";
import Incidents from "./pages/Incidents";
import Reports from "./pages/Reports";

// Import layout components
import AppLayout from "./components/AppLayout";

const queryClient = new QueryClient();

const AppContent = () => {
  const { isAuthenticated, userRole, loading, signOut } = useAuth();

  if (loading) {
    console.log("App: Loading auth state...");
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyber-blue"></div>
      </div>
    );
  }

  console.log("App: Auth state loaded - isAuthenticated:", isAuthenticated, "userRole:", userRole);

  return (
    <Routes>
      {/* Login Route */}
      <Route 
        path="/login" 
        element={!isAuthenticated ? <Login /> : <Navigate to={userRole === "admin" ? "/admin-dashboard" : "/monitoring-dashboard"} replace />}
      />
      
      {/* Protected Routes with Layout */}
      {isAuthenticated ? (
        <Route 
          path="/*" 
          element={
            <SidebarProvider defaultOpen={false}>
              <div className="min-h-screen flex w-full bg-background">
                <AppLayout onLogout={signOut} userRole={userRole}>
                  <Routes>
                    <Route 
                      path="/" 
                      element={<Navigate to={userRole === "admin" ? "/admin-dashboard" : "/monitoring-dashboard"} replace />} 
                    />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/phishing" element={<PhishingEmails />} />
                    <Route path="/ddos" element={<DDoSAttacks />} />
                    <Route path="/brute-force" element={<BruteForce />} />
                    <Route path="/logs" element={<LogsDashboard />} />
                    <Route path="/playbooks" element={<PlaybookConfig />} />
                    <Route path="/incidents" element={<Incidents />} />
                    <Route path="/reports" element={<Reports />} />
                    {userRole === "admin" ? (
                      <>
                        <Route path="/admin-dashboard" element={<AdminDashboard />} />
                        <Route path="/monitoring" element={<MonitoringDashboard />} />
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
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;