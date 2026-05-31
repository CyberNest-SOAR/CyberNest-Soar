import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { SidebarProvider } from "@/components/ui/sidebar";
import { useAuth } from "./hooks/useAuth";

// Import pages
import Login from "./pages/Login";
import LogsDashboard from "./pages/LogsDashboard";
import ThreatIntelligence from "./pages/ThreatIntelligence";
import PlaybookConfig from "./pages/PlaybookConfig";
import MonitoringDashboard from "./pages/MonitoringDashboard";
import AdminDashboard from "./pages/AdminDashboard";

// Import new sub-pages
import CommandCenter from "./pages/soc/CommandCenter";
import AlertsTablePage from "./pages/soc/AlertsTablePage";
import IncidentResponsePage from "./pages/soc/IncidentResponsePage";
import AssetIntelligencePage from "./pages/assets/AssetIntelligencePage";
import ItHygienePage from "./pages/assets/ItHygienePage";
import ThreatIntelCenterPage from "./pages/intel/ThreatIntelCenterPage";
import PlaybooksAutomationPage from "./pages/automation/PlaybooksAutomationPage";
import AiOperationsPage from "./pages/ai/AiOperationsPage";
import AdminHealthPage from "./pages/admin/AdminHealthPage";
import ReportingAuditPage from "./pages/admin/ReportingAuditPage";

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
          element={!isAuthenticated ? <PageTransition><Login /></PageTransition> : <Navigate to={userRole === "admin" ? "/admin/dashboard" : "/assets/endpoint-health"} replace />}
        />
        
        {isAuthenticated ? (
          <Route 
            path="/*" 
            element={
              <SidebarProvider defaultOpen={true}>
                <AppLayout onLogout={signOut} userRole={userRole}>
                  <AnimatePresence mode="wait">
                    <Routes location={location} key={location.pathname}>
                      {/* SOC Group */}
                      <Route path="/dashboard" element={<PageTransition><CommandCenter /></PageTransition>} />
                      <Route path="/soc/command-center" element={<PageTransition><CommandCenter /></PageTransition>} />
                      <Route path="/soc/alert-monitor" element={<PageTransition><LogsDashboard /></PageTransition>} />
                      <Route path="/soc/alert-forensics" element={<PageTransition><AlertsTablePage /></PageTransition>} />
                      <Route path="/soc/incident-response" element={<PageTransition><IncidentResponsePage /></PageTransition>} />

                      {/* Assets Group */}
                      <Route path="/assets/asset-intelligence" element={<PageTransition><AssetIntelligencePage /></PageTransition>} />
                      <Route path="/assets/endpoint-health" element={<PageTransition><MonitoringDashboard /></PageTransition>} />
                      <Route path="/assets/it-hygiene" element={<PageTransition><ItHygienePage /></PageTransition>} />

                      {/* Intel Group */}
                      <Route path="/intel/phishing-center" element={<PageTransition><ThreatIntelligence /></PageTransition>} />
                      <Route path="/intel/threat-intel-center" element={<PageTransition><ThreatIntelCenterPage /></PageTransition>} />

                      {/* Automation Group */}
                      <Route path="/automation/playbooks-config" element={<PageTransition><PlaybookConfig /></PageTransition>} />
                      <Route path="/automation/playbooks-automation" element={<PageTransition><PlaybooksAutomationPage /></PageTransition>} />

                      {/* AI Group */}
                      <Route path="/ai/ai-operations" element={<PageTransition><AiOperationsPage /></PageTransition>} />

                      {/* Admin Group */}
                      <Route path="/admin/dashboard" element={<PageTransition><AdminDashboard /></PageTransition>} />
                      <Route path="/admin/admin-health" element={<PageTransition><AdminHealthPage /></PageTransition>} />
                      <Route path="/admin/reporting-audit" element={<PageTransition><ReportingAuditPage /></PageTransition>} />

                      {/* Backward Compatible Legacy Routes */}
                      <Route path="/threat-intelligence" element={<PageTransition><ThreatIntelligence /></PageTransition>} />
                      <Route path="/logs" element={<Navigate to="/soc/alert-monitor" replace />} />
                      <Route path="/incidents" element={<PageTransition><IncidentResponsePage /></PageTransition>} />
                      <Route path="/reports" element={<PageTransition><ReportingAuditPage /></PageTransition>} />
                      
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
                        element={<Navigate to={userRole === "admin" ? "/admin/dashboard" : "/assets/endpoint-health"} replace />} 
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
