import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
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

import Index from "./pages/Index";
import { CyberLoader } from "./components/CyberLoader";
import { PageTransition } from "./components/PageTransition";
import { AnimatePresence } from "framer-motion";

const AppContent = () => {
  const { isAuthenticated, userRole, loading, signOut } = useAuth();
  const location = useLocation();

  if (loading) {
    return <CyberLoader />;
  }

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<PageTransition><Index /></PageTransition>} />
        <Route 
          path="/login" 
          element={!isAuthenticated ? <PageTransition><Login /></PageTransition> : <Navigate to={userRole === "admin" ? "/admin-dashboard" : "/monitoring-dashboard"} replace />}
        />
        
        {isAuthenticated ? (
          <Route 
            path="/*" 
            element={
              <SidebarProvider defaultOpen={true}>
                <AppLayout onLogout={signOut} userRole={userRole}>
                  <AnimatePresence mode="wait">
                    <Routes location={location} key={location.pathname}>
                      <Route path="/dashboard" element={<PageTransition><Dashboard /></PageTransition>} />
                      <Route path="/threat-intelligence" element={<PageTransition><ThreatIntelligence /></PageTransition>} />
                      <Route path="/logs" element={<PageTransition><LogsDashboard /></PageTransition>} />
                      <Route path="/incidents" element={<PageTransition><Incidents /></PageTransition>} />
                      <Route path="/reports" element={<PageTransition><Reports /></PageTransition>} />
                      {userRole === "admin" ? (
                        <>
                          <Route path="/admin-dashboard" element={<PageTransition><AdminDashboard /></PageTransition>} />
                          <Route path="/monitoring" element={<PageTransition><MonitoringDashboard /></PageTransition>} />
                          <Route path="/playbooks" element={<PageTransition><PlaybookConfig /></PageTransition>} />
                        </>
                      ) : (
                        <Route path="/monitoring-dashboard" element={<PageTransition><MonitoringDashboard /></PageTransition>} />
                      )}
                      <Route 
                        path="*" 
                        element={<Navigate to={userRole === "admin" ? "/admin-dashboard" : "/monitoring-dashboard"} replace />} 
                      />
                    </Routes>
                  </AnimatePresence>
                </AppLayout>
              </SidebarProvider>
            } 
          />
        ) : (
          <Route path="*" element={<Navigate to="/login" replace />} />
        )}
      </Routes>
    </AnimatePresence>
  );
};

import { TopProgressBar } from "./components/TopProgressBar";

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark" storageKey="cybernest-theme">
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <TopProgressBar />
            <AppContent />
          </BrowserRouter>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
