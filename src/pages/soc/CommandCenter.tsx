import { useState } from "react";
import { useDashboardData } from "@/hooks/useDashboardData";
import { PageHeader } from "@/components/PageHeader";
import { CyberCard } from "@/components/CyberCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { 
  Shield, 
  Activity, 
  AlertTriangle, 
  Zap, 
  RefreshCw, 
  Filter, 
  ChevronRight, 
  ExternalLink,
  Target,
  FileText,
  Volume2
} from "lucide-react";
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  PieChart, 
  Pie, 
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from "recharts";
import { toast } from "sonner";
import { useServerStatusContext } from "@/contexts/ServerStatusContext";

interface TopMetrics {
  total_events: number;
  critical_alerts: number;
  high_alerts: number;
  active_campaigns: number;
  suppression_rate: number;
  noise_rate: number;
  false_positive_rate: number;
  true_positive_rate: number;
}

interface RiskItem {
  event_id: string;
  risk_score: number;
  severity: number;
  escalation_level: string;
  analyst_assigned: string;
  asset_criticality: string;
}

interface CommandCenterData {
  page: string;
  top_metrics: TopMetrics;
  severity_distribution: Record<string, number>;
  attack_type_distribution: Record<string, number>;
  mitre_heatmap: Record<string, number>;
  risk_queue: RiskItem[];
  noise_reduction: {
    total_suppressed: number;
    total_noise: number;
    ai_auto_closed: number;
    analyst_verdicts: Record<string, number>;
  };
  campaigns: {
    active: number;
    total_in_sample: number;
  };
}

const fallbackDefault: CommandCenterData = {
  page: "SOC Command Center",
  top_metrics: {
    total_events: 0,
    critical_alerts: 0,
    high_alerts: 0,
    active_campaigns: 0,
    suppression_rate: 0,
    noise_rate: 0,
    false_positive_rate: 0,
    true_positive_rate: 0
  },
  severity_distribution: {},
  attack_type_distribution: {},
  mitre_heatmap: {},
  risk_queue: [],
  noise_reduction: {
    total_suppressed: 0,
    total_noise: 0,
    ai_auto_closed: 0,
    analyst_verdicts: {}
  },
  campaigns: {
    active: 0,
    total_in_sample: 0
  }
};

const API_BASE = "/api/v1";

export default function CommandCenter() {
  const { data, loading, refetch } = useDashboardData<CommandCenterData>("command-center.json", fallbackDefault);
  const { isOnline: backendOnline } = useServerStatusContext();
  const [criticalityFilter, setCriticalityFilter] = useState<string>("all");
  const metrics = data.top_metrics;

  // Format charts data safely
  const severityData = Object.entries(data.severity_distribution || {}).map(([key, val]) => ({
    severity: `Level ${key}`,
    count: val,
    rawSeverity: Number(key)
  })).sort((a, b) => a.rawSeverity - b.rawSeverity);

  const attackData = Object.entries(data.attack_type_distribution || {})
    .filter(([name]) => name !== "benign")
    .map(([name, val]) => ({
      name: name.replace("_", " ").toUpperCase(),
      value: val
    }));

  const COLORS = [
    "hsl(var(--cyber-blue))",
    "hsl(var(--critical))",
    "hsl(var(--warning))",
    "hsl(var(--primary))",
    "hsl(var(--secondary))",
    "hsl(var(--info))",
    "hsl(var(--success))",
    "hsl(var(--accent))",
  ];

  const mitreData = Object.entries(data.mitre_heatmap || {}).map(([key, val]) => ({
    subject: key,
    count: val,
    fullMark: Math.max(...Object.values(data.mitre_heatmap || {}), 1)
  }));

  const filteredRiskQueue = data.risk_queue?.filter(item => {
    if (criticalityFilter === "all") return true;
    return item.asset_criticality === criticalityFilter;
  }) || [];

  // Queue backlog age calculation - mock based on position in queue
  const totalCritical = filteredRiskQueue.length;
  const unassignedCount = filteredRiskQueue.filter(a => !a.analyst_assigned || a.analyst_assigned === "unassigned").length;
  const backlogAgeMinutes = Math.max(5, Math.round(totalCritical * 3.2)); // simulated median age

  const handleInvestigate = (eventId: string) => {
    toast.success("Investigation Initiated", {
      description: `Targeting event ${eventId}. Initializing asset telemetry capture.`,
      icon: <Activity className="h-4 w-4 text-primary" />
    });
  };

  // Skeleton loading screen
  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-12 w-64 bg-muted/40 rounded-lg" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-32 bg-card/30 border border-border/20 rounded-2xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-[350px] bg-card/30 border border-border/20 rounded-2xl" />
          <div className="h-[350px] bg-card/30 border border-border/20 rounded-2xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full space-y-10 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <PageHeader 
          title="SOC Command Center"
          description="Global real-time threat detection telemetry and response dashboard"
          breadcrumbs={[{ label: "SOC" }, { label: "Command Center" }]}
        />
        <div className="flex gap-3 bg-card/40 p-2 rounded-2xl border border-border/40 backdrop-blur-md">
          <Button variant="outline" size="sm" onClick={refetch} className="font-mono text-xs border-border/40 flex items-center gap-2 hover:bg-primary/5">
            <RefreshCw className="h-3.5 w-3.5" /> Force Sync
          </Button>
          <Badge className={`px-3 py-1 text-xs border ${backendOnline === null ? "bg-yellow-500/10 text-yellow-500 border-yellow-500/20" : backendOnline ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-rose-500/10 text-rose-500 border-rose-500/20"}`}>
            <span className={`h-1.5 w-1.5 rounded-full mr-1.5 ${backendOnline === null ? "bg-yellow-500" : backendOnline ? "bg-emerald-500 animate-pulse" : "bg-rose-500"}`} />
            {backendOnline === null ? "CHECKING..." : backendOnline ? "BACKEND ONLINE" : "BACKEND OFFLINE"}
          </Badge>
        </div>
      </div>

      {/* Dynamic Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <CyberCard delay={0.05} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <Activity className="h-5 w-5" />
            </div>
            <Badge variant="outline" className="text-emerald-500 bg-emerald-500/5 border-emerald-500/20 text-[10px]">
              +5.4% (1h)
            </Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Total Global Events</p>
            <h3 className="text-3xl font-black font-mono tracking-tight">{metrics.total_events?.toLocaleString()}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.1} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500">
              <AlertTriangle className="h-5 w-5 animate-pulse" />
            </div>
            <Badge variant="outline" className="text-rose-500 bg-rose-500/5 border-rose-500/20 text-[10px]">
              CRITICAL
            </Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Active Campaigns</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-rose-500">{metrics.active_campaigns}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.15} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-yellow-500/10 border border-yellow-500/20 text-yellow-500">
              <Volume2 className="h-5 w-5" />
            </div>
            <Badge variant="outline" className="text-yellow-500 bg-yellow-500/5 border-yellow-500/20 text-[10px]">
              NOISE RATE
            </Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Signal Deflection Rate</p>
            <h3 className="text-3xl font-black font-mono tracking-tight">{metrics.noise_rate}%</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.2} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-500">
              <Target className="h-5 w-5" />
            </div>
            <Badge variant="outline" className="text-indigo-500 bg-indigo-500/5 border-indigo-500/20 text-[10px]">
              ACCURACY
            </Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">True Positive Yield</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-indigo-400">{metrics.true_positive_rate}%</h3>
          </div>
        </CyberCard>
      </div>

      {/* Visualizations Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Severity Distribution BarChart */}
        <Card className="lg:col-span-2 bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
                  <Activity className="h-4 w-4 text-primary" />
                  Severity Distribution
                </CardTitle>
                <CardDescription>Telemetry event volume analyzed by threat level</CardDescription>
              </div>
              <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20 text-[10px] uppercase font-mono">
                Real-time
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={severityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.1} vertical={false} />
                  <XAxis dataKey="severity" stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      backdropFilter: "blur(12px)",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "12px",
                      color: "hsl(var(--foreground))",
                    }}
                  />
                  <Bar dataKey="count" fill="hsl(var(--cyber-blue))" radius={[6, 6, 0, 0]}>
                    {severityData.map((entry, index) => {
                      const isHighSeverity = entry.rawSeverity >= 8;
                      return (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={isHighSeverity ? "hsl(var(--critical))" : "hsl(var(--cyber-blue))"} 
                          opacity={0.85}
                          className="hover:opacity-100 transition-opacity cursor-pointer"
                        />
                      );
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Attack Type Breakdown */}
        <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <Zap className="h-4 w-4 text-warning" />
              Attack Vectors
            </CardTitle>
            <CardDescription>Distribution of non-benign signature patterns</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 flex flex-col items-center justify-center">
            <div className="h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={attackData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={4}
                  >
                    {attackData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      backdropFilter: "blur(12px)",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "12px",
                      color: "hsl(var(--foreground))",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {/* Inline Legend Grid */}
            <div className="grid grid-cols-2 gap-2.5 w-full mt-4 max-h-[100px] overflow-y-auto custom-scrollbar px-2">
              {attackData.slice(0, 6).map((d, i) => (
                <div key={i} className="flex items-center gap-2 p-1.5 rounded-lg bg-background/30 border border-border/25">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                  <span className="text-[9px] font-mono font-bold truncate tracking-tight uppercase text-muted-foreground">{d.name}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Queue Backlog Monitor */}
        <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Queue Backlog Monitor
            </CardTitle>
            <CardDescription>Triage queue depth and analyst assignment coverage</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-rose-500/5 border border-rose-500/20 rounded-xl p-3 text-center">
                <p className="text-[9px] uppercase tracking-widest text-rose-400/60">Critical Queue</p>
                <p className="text-2xl font-black font-mono text-rose-400 mt-1">{totalCritical}</p>
              </div>
              <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-3 text-center">
                <p className="text-[9px] uppercase tracking-widest text-amber-400/60">Unassigned</p>
                <p className="text-2xl font-black font-mono text-amber-400 mt-1">{unassignedCount}</p>
              </div>
            </div>
            <div className="bg-primary/5 border border-primary/20 rounded-xl p-3">
              <p className="text-[9px] uppercase tracking-widest text-primary/60 mb-1">Median Backlog Age</p>
              <p className="text-xl font-black font-mono text-primary">{backlogAgeMinutes} min</p>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-[10px] text-muted-foreground/60 font-mono">
                <span>SLA Breach Risk</span>
                <span className={backlogAgeMinutes > 10 ? "text-rose-400 font-bold" : "text-emerald-400 font-bold"}>
                  {backlogAgeMinutes > 10 ? "BREACHING" : "WITHIN SLA"}
                </span>
              </div>
              <div className="h-1.5 w-full bg-muted/30 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${backlogAgeMinutes > 10 ? "bg-rose-500" : "bg-emerald-500"}`}
                  style={{ width: `${Math.min((backlogAgeMinutes / 15) * 100, 100)}%` }} />
              </div>
            </div>
            <div className="text-[10px] text-muted-foreground/40 font-mono text-center pt-1">
              15-minute triage SLA threshold
            </div>
          </CardContent>
        </Card>

        {/* Risk Queue Table */}
        <Card className="lg:col-span-2 bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 flex flex-col sm:flex-row sm:items-center justify-between pb-4 gap-4">
            <div>
              <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" />
                Critical Risk Queue
              </CardTitle>
              <CardDescription>Inbound security anomalies waiting for analyst assignment</CardDescription>
            </div>
            
            <div className="flex items-center gap-2">
              <Filter className="h-3.5 w-3.5 text-muted-foreground" />
              <select
                value={criticalityFilter}
                onChange={(e) => setCriticalityFilter(e.target.value)}
                className="bg-background/80 border border-border/40 text-xs px-2.5 py-1 rounded-lg text-foreground focus:ring-1 focus:ring-primary outline-none"
              >
                <option value="all">All Asset Criticalities</option>
                <option value="critical">Critical Only</option>
                <option value="high">High & Critical</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </CardHeader>
          
          <CardContent className="pt-4 px-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-border/30 hover:bg-transparent">
                    <TableHead className="pl-6 font-mono text-[10px] uppercase font-black text-muted-foreground/60 tracking-wider">Event ID</TableHead>
                    <TableHead className="font-mono text-[10px] uppercase font-black text-muted-foreground/60 tracking-wider">Severity</TableHead>
                    <TableHead className="font-mono text-[10px] uppercase font-black text-muted-foreground/60 tracking-wider">Escalation</TableHead>
                    <TableHead className="font-mono text-[10px] uppercase font-black text-muted-foreground/60 tracking-wider">Criticality</TableHead>
                    <TableHead className="font-mono text-[10px] uppercase font-black text-muted-foreground/60 tracking-wider">Assigned</TableHead>
                    <TableHead className="pr-6 text-right font-mono text-[10px] uppercase font-black text-muted-foreground/60 tracking-wider">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRiskQueue.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-10 text-muted-foreground">
                        No critical events in current queue parameters.
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredRiskQueue.slice(0, 5).map((item, idx) => (
                      <TableRow key={idx} className="hover:bg-muted/10 border-border/10">
                        <TableCell className="pl-6 font-mono text-xs font-bold text-foreground">
                          {item.event_id}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className={
                            item.severity >= 12 
                              ? "bg-rose-500/10 text-rose-500 border-rose-500/30" 
                              : item.severity >= 8 
                              ? "bg-orange-500/10 text-orange-500 border-orange-500/30"
                              : "bg-yellow-500/10 text-yellow-500 border-yellow-500/30"
                          }>
                            Level {item.severity}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-[10px] uppercase tracking-wider font-bold">
                          {item.escalation_level}
                        </TableCell>
                        <TableCell>
                          <Badge className={
                            item.asset_criticality === "critical"
                              ? "bg-rose-600/20 text-rose-400 border-rose-500/35"
                              : item.asset_criticality === "high"
                              ? "bg-amber-600/20 text-amber-400 border-amber-500/35"
                              : "bg-blue-600/20 text-blue-400 border-blue-500/35"
                          }>
                            {item.asset_criticality}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-xs font-semibold text-muted-foreground">
                          {item.analyst_assigned}
                        </TableCell>
                        <TableCell className="pr-6 text-right">
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => handleInvestigate(item.event_id)}
                            className="text-[10px] uppercase font-bold text-primary hover:bg-primary/10 tracking-widest h-8"
                          >
                            Investigate
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
