import { useState, useMemo } from "react";
import { useDashboardData } from "@/hooks/useDashboardData";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { 
  Database, 
  Search, 
  Filter, 
  RefreshCw, 
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
  Settings,
  ShieldX
} from "lucide-react";
import { toast } from "sonner";

interface Alert {
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
  alerts: Alert[];
}

const fallbackDefault: AlertsTableData = {
  page: "Alerts & Investigation",
  total: 0,
  returned: 0,
  offset: 0,
  limit: 100,
  alerts: []
};

export default function AlertsTablePage() {
  const { data, loading, refetch } = useDashboardData<AlertsTableData>("alerts-table.json", fallbackDefault);
  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  const handleAction = (eventId: string, actionType: string) => {
    toast.info("Mitigation Applied", {
      description: `Action '${actionType}' triggered for event: ${eventId}`,
      icon: <Settings className="h-4 w-4 text-primary animate-spin" />
    });
  };

  // Filter & Search Logic
  const filteredAlerts = useMemo(() => {
    return (data.alerts || []).filter(alert => {
      const matchesSearch = 
        alert.event_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.attack_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.host?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.mitre_technique?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.source_tool?.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesSeverity = severityFilter === "all" ||
        (severityFilter === "critical" && alert.severity >= 12) ||
        (severityFilter === "high" && alert.severity >= 8 && alert.severity < 12) ||
        (severityFilter === "medium" && alert.severity >= 4 && alert.severity < 8) ||
        (severityFilter === "low" && alert.severity < 4);

      const matchesStatus = statusFilter === "all" || alert.status === statusFilter;

      return matchesSearch && matchesSeverity && matchesStatus;
    });
  }, [data.alerts, searchTerm, severityFilter, statusFilter]);

  // Pagination logic
  const totalPages = Math.ceil(filteredAlerts.length / pageSize) || 1;
  const paginatedAlerts = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredAlerts.slice(start, start + pageSize);
  }, [filteredAlerts, currentPage]);

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-12 w-64 bg-muted/40 rounded-lg" />
        <div className="h-16 bg-card/30 border border-border/20 rounded-xl" />
        <div className="h-[400px] bg-card/30 border border-border/20 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="w-full h-full space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <PageHeader 
          title="SOC Alerts Center"
          description="In-depth audit and forensics database of all ingested network anomalies"
          breadcrumbs={[{ label: "SOC" }, { label: "Alerts Table" }]}
        />
        <Button variant="outline" size="sm" onClick={refetch} className="font-mono text-xs border-border/40 flex items-center gap-2 hover:bg-primary/5">
          <RefreshCw className="h-3.5 w-3.5" /> Reload Database
        </Button>
      </div>

      {/* Filter and Search Controls */}
      <Card className="glass border-border/40 shadow-xl backdrop-blur-md">
        <CardContent className="p-4 flex flex-col md:flex-row gap-4">
          <div className="relative flex-1 group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
            <Input 
              placeholder="Search by Event ID, IP Host, Attack Vector, or Tool..." 
              className="pl-10 bg-background/50 border-border/40 focus:border-primary/50 transition-all text-xs"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>
          
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center gap-2 text-muted-foreground/80 font-mono text-[10px] uppercase font-bold tracking-wider">
              <Filter className="h-3.5 w-3.5" /> Filters:
            </div>
            
            <select
              value={severityFilter}
              onChange={(e) => {
                setSeverityFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-background/80 border border-border/40 text-xs px-2.5 py-1.5 rounded-lg text-foreground focus:ring-1 focus:ring-primary outline-none"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical (Level 12+)</option>
              <option value="high">High (Level 8-11)</option>
              <option value="medium">Medium (Level 4-7)</option>
              <option value="low">Low (Level 0-3)</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-background/80 border border-border/40 text-xs px-2.5 py-1.5 rounded-lg text-foreground focus:ring-1 focus:ring-primary outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="open">Open</option>
              <option value="suppressed">Suppressed</option>
              <option value="closed">Closed</option>
            </select>

            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => {
                setSearchTerm("");
                setSeverityFilter("all");
                setStatusFilter("all");
                setCurrentPage(1);
              }} 
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Main Alert Log Table */}
      <Card className="glass border-border/40 shadow-2xl backdrop-blur-md overflow-hidden">
        <CardHeader className="border-b border-border/40 pb-4 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <Database className="h-5 w-5 text-primary" />
              Ingested Event Registry
            </CardTitle>
            <CardDescription>Forensic catalog detailing threat triggers and assigned analysts</CardDescription>
          </div>
          <Badge className="bg-primary/10 text-primary border border-primary/20 text-xs font-mono font-bold px-3 py-1">
            {filteredAlerts.length.toLocaleString()} Detections
          </Badge>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto max-h-[600px] overflow-y-auto custom-scrollbar">
            <Table>
              <TableHeader>
                <TableRow className="border-border/30 bg-muted/20 hover:bg-transparent">
                  <TableHead className="pl-6 font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Event ID</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Severity</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Vector</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Tactic</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Target IP</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Verdict</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Status</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Tool</TableHead>
                  <TableHead className="pr-6 text-right font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Mitigations</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedAlerts.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center py-12 text-muted-foreground font-semibold">
                      No matching records found in this dataset view.
                    </TableCell>
                  </TableRow>
                ) : (
                  paginatedAlerts.map((alert, idx) => (
                    <TableRow key={idx} className="hover:bg-muted/10 border-border/10">
                      <TableCell className="pl-6 font-mono text-xs font-bold text-foreground">
                        {alert.event_id}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={
                          alert.severity >= 12
                            ? "bg-rose-500/10 text-rose-500 border-rose-500/30"
                            : alert.severity >= 8
                            ? "bg-orange-500/10 text-orange-500 border-orange-500/30"
                            : alert.severity >= 4
                            ? "bg-yellow-500/10 text-yellow-500 border-yellow-500/30"
                            : "bg-blue-500/10 text-blue-500 border-blue-500/30"
                        }>
                          Level {alert.severity}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs font-bold capitalize text-foreground/80">
                        {alert.attack_type.replace("_", " ")}
                      </TableCell>
                      <TableCell>
                        <Badge className="bg-primary/5 text-primary border border-primary/20 text-[9px] font-sans">
                          {alert.mitre_tactic && alert.mitre_tactic !== "None" ? alert.mitre_tactic : "General"}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground font-semibold">
                        {alert.host}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5 text-[10px] font-mono font-bold capitalize">
                          {alert.analyst_verdict === "true_positive" ? (
                            <span className="text-rose-400 flex items-center gap-1"><ShieldAlert size={12} /> True Positive</span>
                          ) : alert.analyst_verdict === "false_positive" ? (
                            <span className="text-emerald-400 flex items-center gap-1"><ShieldCheck size={12} /> False Positive</span>
                          ) : (
                            <span className="text-muted-foreground flex items-center gap-1"><ShieldX size={12} /> Unassigned</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-[10px] uppercase font-bold tracking-wider">
                        <span className={
                          alert.status === "open" 
                            ? "text-rose-500" 
                            : alert.status === "suppressed" 
                            ? "text-yellow-500/80" 
                            : "text-emerald-500"
                        }>
                          {alert.status}
                        </span>
                      </TableCell>
                      <TableCell className="font-mono text-[10px] text-muted-foreground font-bold tracking-wider">
                        {alert.source_tool.replace("synthetic.", "")}
                      </TableCell>
                      <TableCell className="pr-6 text-right">
                        <div className="flex justify-end gap-1.5">
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => handleAction(alert.event_id, "Isolate Host")}
                            className="text-[9px] uppercase font-extrabold text-rose-400 hover:bg-rose-500/10 h-7 tracking-wider"
                          >
                            Isolate
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => handleAction(alert.event_id, "Block IP")}
                            className="text-[9px] uppercase font-extrabold text-primary hover:bg-primary/10 h-7 tracking-wider"
                          >
                            Block
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
          
          {/* Custom Styled Pagination Footer */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between p-4 border-t border-border/40 bg-card/10">
              <div className="text-[10px] text-muted-foreground font-mono">
                Showing Page <span className="font-bold text-foreground">{currentPage}</span> of{" "}
                <span className="font-bold text-foreground">{totalPages}</span> sheets
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8"
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
