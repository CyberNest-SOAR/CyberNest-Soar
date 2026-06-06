import React, { useState, useMemo, useCallback } from "react";
import { 
  Shield, 
  AlertCircle, 
  Activity, 
  Search, 
  Filter, 
  Database,
  RefreshCw,
  AlertTriangle,
  Loader2,
  Eye,
  Terminal,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "sonner";

import { KPICard } from "@/components/logs/KPICard";
import { InvestigationDrawer } from "@/components/logs/InvestigationDrawer";
import { useDashboardData } from "@/hooks/useDashboardData";
import { parseNDJSONStream, type NormalizedAlert } from "@/utils/ndjsonParser";

interface AlertJson {
  event_id: string;
  timestamp: string;
  severity: number;
  risk_score: number;
  mitre_tactic: string | null;
  mitre_technique: string | null;
  source_tool: string;
  attack_type: string;
  host: string;
  dst_host: string;
  user: string | null;
  status: string;
  analyst_verdict: string;
  analyst_assigned: string;
  asset_criticality: string;
  true_positive: boolean;
  noise: boolean;
}

interface AlertsTableData {
  page: string;
  total: number;
  returned: number;
  offset: number;
  limit: number;
  alerts: AlertJson[];
}

const fallbackDefault: AlertsTableData = {
  page: "Alerts & Investigation",
  total: 0,
  returned: 0,
  offset: 0,
  limit: 100,
  alerts: []
};

function jsonToNormalized(j: AlertJson): NormalizedAlert {
  return {
    event_id: j.event_id,
    source: j.source_tool?.replace("synthetic.", "") || "unknown",
    timestamp: j.timestamp,
    description: `${j.attack_type?.replace(/_/g, " ")} detected on ${j.host}${j.mitre_technique && j.mitre_technique !== "None" ? ` (${j.mitre_technique})` : ""}`,
    severity: j.severity,
    host_context: {
      hostname: j.host || "Unknown",
      ip_address: j.host || "N/A",
      mac_address: null,
      os_name: null,
    },
    enrichment_data: {
      risk_score: j.risk_score ?? 0,
      vt_score: 0,
      abuse_score: 0,
      epss_score: null,
      cvss_score: null,
      misp_matches: [],
      tags: [],
      debug_info: {},
    },
    confidence: "-",
    analyst_verdict: j.analyst_verdict,
    analyst_assigned: j.analyst_assigned,
    status: j.status,
  } as any;
}

const LogsDashboard = () => {
  const { data: jsonData, loading: jsonLoading, error: jsonError } = useDashboardData<AlertsTableData>("alerts-table.json", fallbackDefault);
  
  const [ndjsonAlerts, setNdjsonAlerts] = useState<NormalizedAlert[]>([]);
  const [ndjsonLoading, setNdjsonLoading] = useState(false);
  const [ndjsonLoaded, setNdjsonLoaded] = useState(false);
  const [ndjsonError, setNdjsonError] = useState<string | null>(null);

  const combinedAlerts = useMemo<NormalizedAlert[]>(() => {
    if (ndjsonAlerts.length > 0) return ndjsonAlerts;
    return (jsonData?.alerts || []).map(jsonToNormalized);
  }, [ndjsonAlerts, jsonData]);

  const loadNdjson = useCallback(async () => {
    try {
      setNdjsonLoading(true);
      setNdjsonError(null);
      const ndjsonUrl = new URL("/data/soc_dataset_20260522_115145.ndjson", window.location.origin).href;
      const data = await parseNDJSONStream(ndjsonUrl, 10000);
      setNdjsonAlerts(data);
      setNdjsonLoaded(true);
      toast.success("NDJSON Loaded", { description: `${data.length} rich alerts loaded from streaming dataset.` });
    } catch (err: any) {
      console.warn("NDJSON fallback: using JSON data.", err);
      setNdjsonError(err.message || "NDJSON unavailable");
    } finally {
      setNdjsonLoading(false);
    }
  }, []);

  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [selectedAlert, setSelectedAlert] = useState<NormalizedAlert | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const filteredAlerts = useMemo(() => {
    return combinedAlerts.filter((alert: any) => {
      const matchesSearch = searchTerm === "" || 
        alert.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.event_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.host_context?.hostname?.toLowerCase().includes(searchTerm.toLowerCase());

      const severityVal = alert.severity;
      const matchesSeverity = severityFilter === "all" || 
        (severityFilter === "critical" && severityVal >= 12) ||
        (severityFilter === "high" && severityVal >= 8 && severityVal < 12) ||
        (severityFilter === "medium" && severityVal >= 4 && severityVal < 8) ||
        (severityFilter === "low" && severityVal >= 1 && severityVal < 4);

      return matchesSearch && matchesSeverity;
    });
  }, [combinedAlerts, searchTerm, severityFilter]);

  const stats = useMemo(() => {
    const total = combinedAlerts.length;
    const critical = combinedAlerts.filter((a: any) => a.severity >= 12).length;
    const totalRisk = combinedAlerts.reduce((acc: number, a: any) => acc + (a.enrichment_data?.risk_score || 0), 0);
    const avgRisk = total > 0 ? (totalRisk / total).toFixed(1) : "0";
    return { total, critical, avgRisk };
  }, [combinedAlerts]);

  const recentAlerts = useMemo(() => filteredAlerts.slice(0, 15), [filteredAlerts]);

  const handleRowClick = (alert: NormalizedAlert) => {
    setSelectedAlert(alert);
    setIsDrawerOpen(true);
  };

  const severityBadge = (sev: number) => {
    if (sev >= 12) return <Badge className="bg-rose-500/15 text-rose-400 border-rose-500/30 text-[9px]">CRITICAL</Badge>;
    if (sev >= 8) return <Badge className="bg-orange-500/15 text-orange-400 border-orange-500/30 text-[9px]">HIGH</Badge>;
    if (sev >= 4) return <Badge className="bg-amber-500/15 text-amber-400 border-amber-500/30 text-[9px]">MEDIUM</Badge>;
    return <Badge className="bg-blue-500/15 text-blue-400 border-blue-500/30 text-[9px]">LOW</Badge>;
  };

  if (jsonLoading) {
    return (
      <div className="flex flex-col h-[calc(100vh-120px)] w-full overflow-y-auto space-y-8 pr-2 custom-scrollbar pb-12 animate-pulse">
        <div className="flex justify-between items-center">
          <div className="space-y-2"><div className="h-8 w-64 bg-muted/60 rounded-lg" /><div className="h-4 w-96 bg-muted/40 rounded" /></div>
          <div className="h-10 w-32 bg-muted/50 rounded-full" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(n => (
            <div key={n} className="h-32 bg-card/40 border border-border/20 rounded-2xl p-6 space-y-4">
              <div className="flex justify-between"><div className="h-4 w-24 bg-muted/60 rounded" /><div className="h-5 w-5 bg-muted/50 rounded-full" /></div>
              <div className="h-8 w-20 bg-muted/80 rounded-lg" /><div className="h-3.5 w-40 bg-muted/40 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (jsonError && combinedAlerts.length === 0) {
    return (
      <div className="flex h-[calc(100vh-120px)] w-full items-center justify-center">
        <Card className="max-w-md border-destructive/20 bg-destructive/5 shadow-2xl backdrop-blur-sm">
          <CardHeader className="text-center pb-2">
            <AlertTriangle className="h-12 w-12 text-destructive mx-auto animate-bounce mb-2" />
            <CardTitle className="text-lg font-bold text-destructive">Data Load Error</CardTitle>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <p className="text-sm text-muted-foreground leading-relaxed">
              Could not load alert data.<br />
              <span className="font-mono text-xs bg-destructive/10 px-2 py-1 rounded text-destructive mt-2 inline-block">{jsonError}</span>
            </p>
            <Button onClick={() => window.location.reload()} className="mt-2">
              <RefreshCw className="h-4 w-4 mr-2" /> Reload
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-120px)] w-full overflow-hidden gap-0">
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-8 animate-fade-in pb-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
              <Shield className="h-8 w-8 text-primary" />
              Alert Monitor
            </h1>
            <p className="text-muted-foreground mt-1">Real-time monitoring KPIs and recent alerts for quick triage</p>
          </div>
          <div className="flex items-center gap-3">
            {ndjsonLoaded ? (
              <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 text-[10px] gap-1.5 px-3 py-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                RICH DATA ACTIVE
              </Badge>
            ) : ndjsonLoading ? (
              <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/20 text-[10px] gap-1.5 px-3 py-1">
                <Loader2 className="h-3 w-3 animate-spin" />
                LOADING NDJSON
              </Badge>
            ) : (
              <Badge variant="outline" className="text-[10px] text-muted-foreground/60 px-3 py-1">
                JSON MODE
              </Badge>
            )}
            <Button variant="outline" size="sm" onClick={loadNdjson} disabled={ndjsonLoading}
              className="font-mono text-xs hover:bg-primary/5 flex items-center gap-2">
              <RefreshCw className={`h-3 w-3 ${ndjsonLoading ? "animate-spin" : ""}`} /> 
              {ndjsonLoaded ? "Reload NDJSON" : "Load Rich Data"}
            </Button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <KPICard 
            title="Total Alerts Loaded" 
            value={stats.total.toLocaleString()} 
            description={ndjsonLoaded ? "NDJSON streaming dataset" : "JSON static dataset"}
            icon={Activity}
            colorClass="bg-blue-500 text-blue-500"
          />
          <KPICard 
            title="Critical Alerts" 
            value={stats.critical.toLocaleString()} 
            description="Severe threats requiring immediate response"
            icon={AlertCircle}
            colorClass="bg-red-500 text-red-500"
          />
          <KPICard 
            title="Average Risk Score" 
            value={stats.avgRisk} 
            description="Mean risk across all loaded alerts"
            icon={Shield}
            colorClass="bg-purple-500 text-purple-500"
          />
        </div>

        {/* Search Bar */}
        <Card className="glass border-border/40 shadow-xl">
          <CardContent className="p-4 flex flex-col md:flex-row gap-4">
            <div className="relative flex-1 group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
              <Input 
                placeholder="Search alerts by event ID, description, or host..." 
                className="pl-10 bg-background/50 border-border/40 focus:border-primary/50 transition-all text-xs"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div className="flex flex-wrap gap-4 items-center">
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-widest">Severity:</span>
              </div>
              <select value={severityFilter} onChange={e => setSeverityFilter(e.target.value)}
                className="bg-background/50 border border-border/30 text-xs px-2.5 py-1.5 rounded-lg text-foreground focus:ring-1 focus:ring-primary outline-none">
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <Button variant="ghost" size="sm" onClick={() => { setSearchTerm(""); setSeverityFilter("all"); }}
                className="text-xs text-muted-foreground hover:text-foreground">
                Reset
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Recent Alerts (compact, no pagination) */}
        <Card className="glass border-border/40 shadow-xl backdrop-blur-md overflow-hidden">
          <CardHeader className="border-b border-border/40 pb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-bold flex items-center gap-2">
                <Terminal className="h-4 w-4 text-primary" />
                Recent Alerts
              </CardTitle>
              <Badge className="bg-muted/30 text-muted-foreground/70 border-border/20 text-[10px] font-mono">
                {filteredAlerts.length} available · showing 15
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto max-h-[420px] overflow-y-auto custom-scrollbar">
              <Table>
                <TableHeader>
                  <TableRow className="border-border/20 bg-muted/10 hover:bg-transparent">
                    <TableHead className="pl-4 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Event</TableHead>
                    <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Severity</TableHead>
                    <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Description</TableHead>
                    <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Host</TableHead>
                    <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Source</TableHead>
                    <TableHead className="pr-4 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentAlerts.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-12 text-muted-foreground/50 font-mono text-xs">
                        No alerts match the current filters.
                      </TableCell>
                    </TableRow>
                  ) : recentAlerts.map((alert: any, idx: number) => (
                    <TableRow key={alert.event_id || idx}
                      className="hover:bg-muted/10 border-border/10 cursor-pointer"
                      onClick={() => handleRowClick(alert)}>
                      <TableCell className="pl-4 font-mono text-[10px] font-bold text-foreground/70 max-w-[140px] truncate">
                        {alert.event_id}
                      </TableCell>
                      <TableCell>{severityBadge(alert.severity)}</TableCell>
                      <TableCell className="text-[10px] text-muted-foreground/80 max-w-[260px] truncate">
                        {alert.description}
                      </TableCell>
                      <TableCell className="font-mono text-[10px] text-foreground/60">
                        {alert.host_context?.hostname || alert.host_context?.ip_address}
                      </TableCell>
                      <TableCell className="font-mono text-[10px] text-muted-foreground/50">
                        {alert.source}
                      </TableCell>
                      <TableCell className="pr-4 text-right">
                        <Button variant="ghost" size="sm" className="h-6 text-[9px] gap-1 text-primary hover:bg-primary/10">
                          <Eye className="h-3 w-3" /> Investigate
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      <InvestigationDrawer 
        alert={selectedAlert}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />
    </div>
  );
};

export default LogsDashboard;
