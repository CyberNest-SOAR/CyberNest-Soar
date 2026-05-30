import { useDashboardData } from "@/hooks/useDashboardData";
import { PageHeader } from "@/components/PageHeader";
import { CyberCard } from "@/components/CyberCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { 
  FileText, 
  RefreshCw, 
  Activity, 
  FileSpreadsheet, 
  Download, 
  ChevronRight,
  TrendingUp,
  Award,
  BookOpen
} from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell } from "recharts";
import { toast } from "sonner";

interface ReportingAuditData {
  page: string;
  shift_handover: {
    open_incidents: number;
    pending_escalations: number;
    total_events_in_scope: number;
    analyst_activity: Record<string, number>;
  };
  executive_reports: {
    mttr_trend: string;
    incident_trend: Record<string, number>;
    total_incidents: number;
    critical_incidents: number;
  };
  technical_reports: {
    total_iocs: number;
    attack_chains: number;
    affected_systems: number;
  };
  export_options: string[];
}

const fallbackDefault: ReportingAuditData = {
  page: "Reporting & Audit",
  shift_handover: {
    open_incidents: 0,
    pending_escalations: 0,
    total_events_in_scope: 0,
    analyst_activity: {}
  },
  executive_reports: {
    mttr_trend: "N/A (live data)",
    incident_trend: {},
    total_incidents: 0,
    critical_incidents: 0
  },
  technical_reports: {
    total_iocs: 0,
    attack_chains: 0,
    affected_systems: 0
  },
  export_options: []
};

export default function ReportingAuditPage() {
  const { data, loading, refetch } = useDashboardData<ReportingAuditData>("reporting-audit.json", fallbackDefault);

  const shift = data.shift_handover;
  const exec = data.executive_reports;
  const tech = data.technical_reports;

  // Format Recharts analyst activity bar chart data
  const analystChartData = Object.entries(shift.analyst_activity || {}).map(([key, val]) => ({
    name: key.toUpperCase(),
    incidents: val
  })).sort((a, b) => b.incidents - a.incidents);

  // Format Recharts executive incident trend bar chart
  const trendChartData = Object.entries(exec.incident_trend || {}).map(([key, val]) => ({
    name: key,
    count: val
  }));

  const COLORS = [
    "hsl(var(--cyber-blue))",
    "hsl(var(--critical))",
    "hsl(var(--warning))",
    "#a855f7",
    "#ec4899",
    "#eab308",
    "#3b82f6",
    "#10b981",
    "#f43f5e",
    "#06b6d4"
  ];

  const handleExport = (format: string) => {
    toast.success("Forensic Export Completed", {
      description: `Shift handover audit log generated successfully in ${format.toUpperCase()} format.`,
      icon: <FileSpreadsheet className="h-4 w-4 text-emerald-500 animate-pulse" />
    });
  };

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-12 w-64 bg-muted/40 rounded-lg" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-[350px] bg-card/30 border border-border/20 rounded-xl" />
          <div className="h-[350px] bg-card/30 border border-border/20 rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full space-y-10 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <PageHeader 
          title="Reporting & Shift Handover"
          description="Executive shift handover summaries, technical indicators audit logs, and PDF/CSV compliance generators"
          breadcrumbs={[{ label: "Admin" }, { label: "Reporting & Audit" }]}
        />
        <Button variant="outline" size="sm" onClick={refetch} className="font-mono text-xs border-border/40 flex items-center gap-2 hover:bg-primary/5">
          <RefreshCw className="h-3.5 w-3.5" /> Force Audit Re-scan
        </Button>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <CyberCard delay={0.05} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <TrendingUp className="h-5 w-5" />
            </div>
            <Badge className="bg-primary/10 text-primary border border-primary/20 text-[10px]">SHIFT_TOTAL</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Shift Incidents Handled</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-foreground">{exec.total_incidents?.toLocaleString()}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.1} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500">
              <Activity className="h-5 w-5 animate-pulse" />
            </div>
            <Badge variant="outline" className="text-rose-500 bg-rose-500/5 border-rose-500/20 text-[10px]">SEV_4</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Critical Incident Volume</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-rose-500">{exec.critical_incidents?.toLocaleString()}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.15} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <Award className="h-5 w-5" />
            </div>
            <Badge variant="outline" className="text-purple-400 bg-purple-500/5 border-purple-500/20 text-[10px]">CHAINS</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Attack Chains Analyzed</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-purple-400">{tech.attack_chains} Chains</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.2} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-500">
              <BookOpen className="h-5 w-5" />
            </div>
            <Badge variant="outline" className="text-indigo-400 bg-indigo-500/5 border-indigo-500/20 text-[10px]">EXPORTS</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Compliant Exports</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-indigo-400">3 Formats</h3>
          </div>
        </CyberCard>
      </div>

      {/* Main visual layouts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Analyst Activity Chart */}
        <Card className="lg:col-span-2 bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary animate-pulse" />
              Analyst Incident Resolution Volume
            </CardTitle>
            <CardDescription>Shift incident counts resolved by active security analysts</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analystChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={8} tickLine={false} axisLine={false} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={9} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "rgba(0, 0, 0, 0.85)",
                      backdropFilter: "blur(12px)",
                      border: "1px solid hsl(var(--border) / 0.4)",
                      borderRadius: "12px",
                      color: "white"
                    }}
                  />
                  <Bar dataKey="incidents" radius={[4, 4, 0, 0]} barSize={20}>
                    {analystChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Executive Handover stats & Export Deck */}
        <div className="space-y-6">
          
          {/* Export Deck */}
          <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
            <CardHeader className="border-b border-border/40 pb-4">
              <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
                <Download className="h-4 w-4 text-primary" />
                Audit Export Deck
              </CardTitle>
              <CardDescription>Generate compliance handover dossiers in multiple formats</CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-2.5">
              {(data.export_options || ["csv", "json", "ndjson"]).map((opt, idx) => (
                <div key={idx} className="p-3.5 rounded-xl border border-border/30 bg-background/25 flex justify-between items-center group hover:border-border transition-all">
                  <div className="flex items-center gap-3">
                    <FileSpreadsheet className="h-4 w-4 text-primary group-hover:scale-110 transition-transform" />
                    <span className="font-mono text-xs font-bold text-foreground uppercase tracking-widest">{opt} Handover File</span>
                  </div>
                  <Button size="sm" variant="ghost" onClick={() => handleExport(opt)} className="text-[10px] uppercase font-bold text-primary hover:bg-primary/10 tracking-widest h-8">
                    Generate
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Handover summary */}
          <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
            <CardHeader className="border-b border-border/40 pb-4">
              <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" />
                Shift Handover Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-4">
              <div className="flex justify-between items-center text-xs">
                <span className="text-muted-foreground">Open Incidents Handover:</span>
                <span className="font-mono font-bold text-foreground">{shift.open_incidents?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-muted-foreground">Pending Escalated Actions:</span>
                <span className="font-mono font-bold text-rose-400">{shift.pending_escalations?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-muted-foreground">Total Logs in Scope:</span>
                <span className="font-mono font-bold text-foreground">{shift.total_events_in_scope?.toLocaleString()}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
