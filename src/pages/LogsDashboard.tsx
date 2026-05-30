import React, { useState, useMemo, useEffect } from "react";
import { 
  Shield, 
  AlertCircle, 
  Activity, 
  Search, 
  Filter, 
  ArrowRight,
  Database,
  Info,
  Clock,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  RefreshCw,
  SlidersHorizontal,
  AlertTriangle
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Import custom components
import { KPICard } from "@/components/logs/KPICard";
import { AlertTable } from "@/components/logs/AlertTable";
import { InvestigationDrawer } from "@/components/logs/InvestigationDrawer";

// Import Streaming NDJSON Parser & Dataset asset URL
// @ts-ignore
import ndjsonUrl from "@/soc_dataset_20260522_115145.ndjson?url";
import { parseNDJSONStream } from "@/utils/ndjsonParser";

const LogsDashboard = () => {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [selectedAlert, setSelectedAlert] = useState<any | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  // 1. Asynchronous NDJSON streaming on initial mount
  const loadAlertsData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Fetch and stream-parse the first 10,000 alerts for highly performant client-side use
      const data = await parseNDJSONStream(ndjsonUrl, 10000);
      setAlerts(data);
      setIsLoading(false);
    } catch (err: any) {
      console.error("Failed to load NDJSON dataset:", err);
      setError(err.message || "Failed to parse NDJSON dataset.");
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAlertsData();
  }, []);

  // 2. Reset pagination to page 1 automatically when search terms or filters are updated
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, severityFilter, sourceFilter]);

  // Filtering logic
  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert: any) => {
      const matchesSearch = searchTerm === "" || 
        alert.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.event_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.host_context?.hostname?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.host_context?.ip_address?.toLowerCase().includes(searchTerm.toLowerCase());

      const severityVal = alert.severity;
      const matchesSeverity = severityFilter === "all" || 
        (severityFilter === "critical" && severityVal >= 12) ||
        (severityFilter === "high" && severityVal >= 8 && severityVal < 12) ||
        (severityFilter === "medium" && severityVal >= 4 && severityVal < 8) ||
        (severityFilter === "low" && severityVal >= 1 && severityVal < 4);

      const matchesSource = sourceFilter === "all" || alert.source === sourceFilter;

      return matchesSearch && matchesSeverity && matchesSource;
    });
  }, [alerts, searchTerm, severityFilter, sourceFilter]);

  // KPI Calculations
  const stats = useMemo(() => {
    const total = alerts.length;
    const critical = alerts.filter((a: any) => a.severity >= 12).length;
    const totalRisk = alerts.reduce((acc: number, a: any) => acc + (a.enrichment_data?.risk_score || 0), 0);
    const avgRisk = total > 0 ? (totalRisk / total).toFixed(1) : 0;

    return { total, critical, avgRisk };
  }, [alerts]);

  // Unique sources for filter
  const sources = useMemo(() => {
    const uniqueSources = new Set(alerts.map((a: any) => a.source));
    return Array.from(uniqueSources);
  }, [alerts]);

  // 3. Client-side Pagination Slicing
  const totalItems = filteredAlerts.length;
  const totalPages = Math.ceil(totalItems / pageSize) || 1;

  const paginatedAlerts = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return filteredAlerts.slice(startIndex, startIndex + pageSize);
  }, [filteredAlerts, currentPage, pageSize]);

  const handleRowClick = (alert: any) => {
    setSelectedAlert(alert);
    setIsDrawerOpen(true);
  };

  // Helper to render pagination numbers with ellipses for neat visual layouts
  const pageNumbers = useMemo(() => {
    const range = [];
    const maxVisiblePages = 5;
    let start = Math.max(1, currentPage - 2);
    let end = Math.min(totalPages, start + maxVisiblePages - 1);

    if (end - start < maxVisiblePages - 1) {
      start = Math.max(1, end - maxVisiblePages + 1);
    }

    for (let i = start; i <= end; i++) {
      range.push(i);
    }
    return range;
  }, [currentPage, totalPages]);

  // A. LOADING STATE - Shimmer Skeletal screens for high-end feel
  if (isLoading) {
    return (
      <div className="flex flex-col h-[calc(100vh-120px)] w-full overflow-y-auto space-y-8 pr-2 custom-scrollbar pb-12 animate-pulse">
        {/* Header Shimmer */}
        <div className="flex justify-between items-center">
          <div className="space-y-2">
            <div className="h-8 w-64 bg-muted/60 rounded-lg" />
            <div className="h-4 w-96 bg-muted/40 rounded" />
          </div>
          <div className="h-10 w-32 bg-muted/50 rounded-full" />
        </div>

        {/* KPIs Shimmer */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-32 bg-card/40 border border-border/20 rounded-2xl p-6 space-y-4">
              <div className="flex justify-between">
                <div className="h-4 w-24 bg-muted/60 rounded" />
                <div className="h-5 w-5 bg-muted/50 rounded-full" />
              </div>
              <div className="h-8 w-20 bg-muted/80 rounded-lg" />
              <div className="h-3.5 w-40 bg-muted/40 rounded" />
            </div>
          ))}
        </div>

        {/* Filter Shimmer */}
        <div className="h-16 bg-card/30 border border-border/20 rounded-xl p-4 flex gap-4">
          <div className="h-full flex-1 bg-muted/40 rounded" />
          <div className="h-full w-32 bg-muted/40 rounded" />
          <div className="h-full w-32 bg-muted/40 rounded" />
        </div>

        {/* Table Shimmer */}
        <div className="border border-border/20 bg-card/20 rounded-xl overflow-hidden flex-1 min-h-[300px]">
          <div className="h-10 bg-muted/40 border-b border-border/10" />
          {[1, 2, 3, 4, 5].map((n) => (
            <div key={n} className="h-12 border-b border-border/10 flex items-center px-6 gap-4">
              <div className="h-4 w-20 bg-muted/55 rounded" />
              <div className="h-4 w-12 bg-muted/55 rounded-full" />
              <div className="h-4 w-28 bg-muted/55 rounded" />
              <div className="h-4 flex-1 bg-muted/40 rounded" />
              <div className="h-4 w-24 bg-muted/55 rounded" />
              <div className="h-4 w-16 bg-muted/55 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // B. ERROR STATE - Beautiful error card with reload actions
  if (error) {
    return (
      <div className="flex h-[calc(100vh-120px)] w-full items-center justify-center">
        <Card className="max-w-md border-destructive/20 bg-destructive/5 shadow-2xl backdrop-blur-sm">
          <CardHeader className="text-center pb-2">
            <AlertTriangle className="h-12 w-12 text-destructive mx-auto animate-bounce mb-2" />
            <CardTitle className="text-lg font-syne font-bold text-destructive">Dataset Load Error</CardTitle>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <p className="text-sm text-muted-foreground leading-relaxed">
              We encountered a network or structural error parsing the SOC logs dataset:<br />
              <span className="font-mono text-xs bg-destructive/10 px-2 py-1 rounded text-destructive mt-2 inline-block max-w-full truncate">{error}</span>
            </p>
            <div className="flex justify-center pt-2">
              <Button onClick={loadAlertsData} className="btn-primary flex items-center gap-2">
                <RefreshCw className="h-4 w-4" /> Retry Stream Parse
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // C. RENDER SOC DASHBOARD
  return (
    <div className="flex h-[calc(100vh-120px)] w-full overflow-hidden gap-0">
      {/* Main Dashboard Content */}
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-8 animate-fade-in pb-12">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h1 className="text-3xl font-bold font-syne text-foreground flex items-center gap-3">
              <Shield className="h-8 w-8 text-primary" />
              Alert Center
            </h1>
            <p className="text-muted-foreground mt-1">Real-time security event monitoring and investigation</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-medium">
              <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
              LIVE DATA STREAMING ACTIVE
            </div>
            <Button variant="outline" size="sm" onClick={loadAlertsData} className="font-mono text-xs hover:bg-primary/5 flex items-center gap-2">
              <RefreshCw className="h-3 w-3" /> RELOAD DATA
            </Button>
          </div>
        </div>

        {/* KPI Cards Section */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <KPICard 
            title="Total Alerts Loaded" 
            value={stats.total.toLocaleString()} 
            description="Consolidated rolling buffer"
            icon={Activity}
            colorClass="bg-blue-500 text-blue-500"
          />
          <KPICard 
            title="Critical Alerts" 
            value={stats.critical.toLocaleString()} 
            description="Severe threats requiring response"
            icon={AlertCircle}
            colorClass="bg-red-500 text-red-500"
          />
          <KPICard 
            title="Average Risk Score" 
            value={stats.avgRisk} 
            description="Calculated across parsed stream"
            icon={Shield}
            colorClass="bg-purple-500 text-purple-500"
          />
        </div>

        {/* Filter and Search Bar */}
        <Card className="glass border-border/40 shadow-xl">
          <CardContent className="p-4 flex flex-col md:flex-row gap-4">
            <div className="relative flex-1 group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
              <Input 
                placeholder="Search by Event ID, Signature/Description, IP, or Host..." 
                className="pl-10 bg-background/50 border-border/40 focus:border-primary/50 transition-all"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            
            <div className="flex flex-wrap gap-4 items-center">
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-widest">Filters:</span>
              </div>
              
              <Select value={severityFilter} onValueChange={setSeverityFilter}>
                <SelectTrigger className="w-[140px] bg-background/50 border-border/40 text-xs text-foreground">
                  <SelectValue placeholder="Severity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Severities</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>

              <Select value={sourceFilter} onValueChange={setSourceFilter}>
                <SelectTrigger className="w-[140px] bg-background/50 border-border/40 text-xs text-foreground">
                  <SelectValue placeholder="Source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Sources</SelectItem>
                  {sources.map((source: any) => (
                    <SelectItem key={source} value={source}>{source}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Button variant="ghost" size="sm" onClick={() => {
                setSearchTerm("");
                setSeverityFilter("all");
                setSourceFilter("all");
              }} className="text-xs text-muted-foreground hover:text-foreground">
                Reset
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Alert Table Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-syne font-bold flex items-center gap-2">
              <Database className="h-5 w-5 text-secondary" />
              Alert Logs
              <span className="text-xs font-mono font-normal text-muted-foreground ml-2 px-2 py-0.5 rounded bg-muted/30">
                {filteredAlerts.length} matching
              </span>
            </h2>
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
               <span className="flex items-center gap-1"><Info className="h-3 w-3" /> Select row to investigate | Click copy icon to save raw</span>
            </div>
          </div>

          <AlertTable 
            alerts={paginatedAlerts} 
            onRowClick={handleRowClick}
            selectedAlertId={selectedAlert?.event_id}
          />
          
          {/* DYNAMIC PAGINATION CONTROLS */}
          {totalPages > 1 && (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-4 px-2 border-t border-border/10">
              {/* Left description */}
              <div className="text-xs text-muted-foreground font-mono">
                Showing <span className="font-bold text-foreground">{((currentPage - 1) * pageSize) + 1}</span> to{" "}
                <span className="font-bold text-foreground">{Math.min(currentPage * pageSize, totalItems)}</span> of{" "}
                <span className="font-bold text-foreground">{totalItems.toLocaleString()}</span> entries
              </div>
              
              {/* Pagination controls */}
              <div className="flex items-center gap-6">
                {/* Page Size Selector */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground font-mono">Rows per page:</span>
                  <Select 
                    value={String(pageSize)} 
                    onValueChange={(val) => {
                      setPageSize(Number(val));
                      setCurrentPage(1);
                    }}
                  >
                    <SelectTrigger className="w-[70px] h-8 bg-background/50 border-border/20 text-xs">
                      <SelectValue placeholder="50" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="25">25</SelectItem>
                      <SelectItem value="50">50</SelectItem>
                      <SelectItem value="100">100</SelectItem>
                      <SelectItem value="250">250</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Page numbers / Navigation */}
                <div className="flex items-center gap-1">
                  {/* First Page */}
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-8 w-8 p-0"
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage(1)}
                  >
                    <ChevronsLeft className="h-4 w-4" />
                  </Button>
                  
                  {/* Prev */}
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-8 w-8 p-0"
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>

                  {/* Number buttons */}
                  {pageNumbers[0] > 1 && (
                    <>
                      <Button
                        variant={currentPage === 1 ? "default" : "outline"}
                        className="h-8 w-8 text-xs p-0"
                        onClick={() => setCurrentPage(1)}
                      >
                        1
                      </Button>
                      {pageNumbers[0] > 2 && <span className="text-muted-foreground text-xs px-1">...</span>}
                    </>
                  )}

                  {pageNumbers.map(page => (
                    <Button
                      key={page}
                      variant={currentPage === page ? "default" : "outline"}
                      className={`h-8 w-8 text-xs p-0 transition-all ${currentPage === page ? 'shadow-md shadow-primary/20' : ''}`}
                      onClick={() => setCurrentPage(page)}
                    >
                      {page}
                    </Button>
                  ))}

                  {pageNumbers[pageNumbers.length - 1] < totalPages && (
                    <>
                      {pageNumbers[pageNumbers.length - 1] < totalPages - 1 && <span className="text-muted-foreground text-xs px-1">...</span>}
                      <Button
                        variant={currentPage === totalPages ? "default" : "outline"}
                        className="h-8 w-8 text-xs p-0"
                        onClick={() => setCurrentPage(totalPages)}
                      >
                        {totalPages}
                      </Button>
                    </>
                  )}

                  {/* Next */}
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-8 w-8 p-0"
                    disabled={currentPage === totalPages}
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                  
                  {/* Last Page */}
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-8 w-8 p-0"
                    disabled={currentPage === totalPages}
                    onClick={() => setCurrentPage(totalPages)}
                  >
                    <ChevronsRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Investigation Drawer - Now part of flex flow */}
      <InvestigationDrawer 
        alert={selectedAlert}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />
    </div>
  );
};

export default LogsDashboard;
