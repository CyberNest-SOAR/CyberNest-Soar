import { useState } from "react";
import { useDashboardData } from "@/hooks/useDashboardData";
import { PageHeader } from "@/components/PageHeader";
import { CyberCard } from "@/components/CyberCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  AlertTriangle, 
  Workflow, 
  UserX, 
  Globe, 
  ShieldAlert, 
  CheckCircle,
  FileCheck,
  ChevronDown,
  ChevronUp,
  Cpu,
  RefreshCw,
  Terminal
} from "lucide-react";
import { toast } from "sonner";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { ConfirmActionDialog } from "@/components/ConfirmActionDialog";

interface CaseItem {
  title: string;
  severity: number;
  tags: string[];
  observables_count: number;
  tasks_total: number;
  tasks_pending: number;
  description_preview: string;
}

interface IncidentResponseData {
  page: string;
  case_queue: CaseItem[];
  stats: {
    total_cases: number;
    critical_cases: number;
    cases_by_severity: Record<string, number>;
    top_tags: Record<string, number>;
    escalated_incidents: number;
  };
  response_actions_available: string[];
}

const fallbackDefault: IncidentResponseData = {
  page: "Incident Response",
  case_queue: [],
  stats: {
    total_cases: 0,
    critical_cases: 0,
    cases_by_severity: {},
    top_tags: {},
    escalated_incidents: 0
  },
  response_actions_available: []
};

export default function IncidentResponsePage() {
  const { data, loading, refetch } = useDashboardData<IncidentResponseData>("incident-response.json", fallbackDefault);
  const [selectedCaseIdx, setSelectedCaseIdx] = useState<number | null>(null);

  const [confirmAction, setConfirmAction] = useState<{ target: string; actionName: string } | null>(null);

  const stats = data.stats;
  const actions = data.response_actions_available || [];

  // Recharts Tag statistics mapping
  const tagChartData = Object.entries(stats.top_tags || {})
    .filter(([name]) => name !== "soc-dataset")
    .map(([name, count]) => ({
      name: name.replace("synthetic.", "").toUpperCase(),
      count
    })).slice(0, 7);

  const handleMitigate = (target: string, actionName: string) => {
    setConfirmAction({ target, actionName });
  };

  const executeMitigation = ({ reason, ticketId }: { reason: string; ticketId: string }) => {
    if (!confirmAction) return;
    toast.success("Incident Mitigated", {
      description: `Countermeasure '${confirmAction.actionName}' dispatched to ${confirmAction.target}. Reason: ${reason}${ticketId ? ` | Ticket: ${ticketId}` : ""}`,
      icon: <CheckCircle className="h-4 w-4 text-emerald-500 animate-pulse" />
    });
  };

  const getSeverityLabel = (sev: number) => {
    if (sev >= 4) return { label: "CRITICAL", color: "bg-rose-500/20 text-rose-400 border-rose-500/50" };
    if (sev >= 3) return { label: "HIGH", color: "bg-orange-500/20 text-orange-400 border-orange-500/50" };
    return { label: "MEDIUM", color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/50" };
  };

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-12 w-64 bg-muted/40 rounded-lg" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="h-32 bg-card/30 border border-border/20 rounded-2xl" />
          <div className="h-32 bg-card/30 border border-border/20 rounded-2xl" />
          <div className="h-32 bg-card/30 border border-border/20 rounded-2xl" />
        </div>
        <div className="h-[300px] bg-card/30 border border-border/20 rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="w-full h-full space-y-10 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <PageHeader 
          title="Incident Response Queue"
          description="Interactive case remediation, host containment, and incident lifecycle management"
          breadcrumbs={[{ label: "SOC" }, { label: "Incident Response" }]}
        />
        <Button variant="outline" size="sm" onClick={refetch} className="font-mono text-xs border-border/40 flex items-center gap-2 hover:bg-primary/5">
          <RefreshCw className="h-3.5 w-3.5" /> Sync Cases
        </Button>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <CyberCard delay={0.05} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <Badge className="bg-primary/10 text-primary border border-primary/20 text-[10px]">ACTIVE</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Open Cases</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-foreground">{stats.total_cases}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.1} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500">
              <AlertTriangle className="h-5 w-5 animate-pulse" />
            </div>
            <Badge variant="outline" className="text-rose-500 bg-rose-500/5 border-rose-500/20 text-[10px]">SEV_4</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Critical Detections</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-rose-500">{stats.critical_cases}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.15} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-500">
              <Workflow className="h-5 w-5 animate-pulse" />
            </div>
            <Badge variant="outline" className="text-amber-500 bg-amber-500/5 border-amber-500/20 text-[10px]">INTEGRATION</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Escalated Incidents</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-amber-400">{stats.escalated_incidents?.toLocaleString()}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.2} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-500">
              <Cpu className="h-5 w-5" />
            </div>
            <Badge variant="outline" className="text-indigo-500 bg-indigo-500/5 border-indigo-500/20 text-[10px]">SOAR CORE</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Remediation Rules</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-indigo-400">{actions.length} Options</h3>
          </div>
        </CyberCard>
      </div>

      {/* Case queue + detailed investigation layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Active Cases Queue */}
        <Card className="lg:col-span-2 bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <Terminal className="h-4 w-4 text-primary" />
              Active Incident Queue
            </CardTitle>
            <CardDescription>Select any case row below to initialize active containment controls</CardDescription>
          </CardHeader>
          
          <CardContent className="pt-4 px-0">
            <div className="space-y-2 max-h-[500px] overflow-y-auto custom-scrollbar px-6">
              {(data.case_queue || []).map((c, i) => {
                const isSelected = selectedCaseIdx === i;
                const sevMeta = getSeverityLabel(c.severity);
                return (
                  <div
                    key={i}
                    onClick={() => setSelectedCaseIdx(isSelected ? null : i)}
                    className={`p-4 rounded-xl border transition-all duration-300 cursor-pointer flex flex-col gap-3 group
                      ${
                        isSelected 
                          ? "bg-primary/5 border-primary shadow-[0_0_15px_rgba(59,130,246,0.1)]" 
                          : "bg-background/20 border-border/30 hover:border-border hover:bg-background/40"
                      }`}
                  >
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                      <div className="flex items-center gap-3">
                        <Badge className={sevMeta.color}>{sevMeta.label}</Badge>
                        <h4 className="font-bold text-sm text-foreground font-sans leading-none">{c.title}</h4>
                      </div>
                      <span className="text-[10px] font-mono font-bold text-muted-foreground/60">
                        Tasks: {c.tasks_total - c.tasks_pending}/{c.tasks_total} Compl.
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-1.5">
                      {c.tags.slice(0, 4).map((tag, idx) => (
                        <Badge key={idx} variant="outline" className="text-[9px] uppercase tracking-wider font-mono bg-background/50 border-border/30 text-muted-foreground">
                          {tag.replace("synthetic.", "")}
                        </Badge>
                      ))}
                    </div>

                    {isSelected && (
                      <div className="pt-2 border-t border-border/20 space-y-3 animate-in fade-in-30 slide-in-from-top-1 duration-200">
                        <p className="text-xs font-mono text-muted-foreground bg-black/30 p-3 rounded-lg border border-border/10 whitespace-pre-wrap">
                          {c.description_preview}
                        </p>
                        
                        {/* Observable Metadata */}
                        <div className="flex justify-between items-center text-[10px] text-muted-foreground font-mono">
                          <span>Observables Tracked: {c.observables_count} IP/Hash</span>
                          <span>Pending Checklist: {c.tasks_pending} items</span>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Countermeasures & Stats Column */}
        <div className="space-y-6">
          
          {/* Visual containment controls */}
          <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
            <CardHeader className="border-b border-border/40 pb-4">
              <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-rose-500" />
                Remediation Deck
              </CardTitle>
              <CardDescription>Dispatch containment commands directly to host nodes</CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-3">
              {selectedCaseIdx === null ? (
                <div className="text-center py-6 text-xs text-muted-foreground font-mono border border-dashed border-border/30 rounded-xl p-4">
                  Select an active incident queue case to enable threat mitigations.
                </div>
              ) : (
                <div className="space-y-2.5">
                  <div className="text-[10px] uppercase font-bold text-muted-foreground font-mono mb-2">
                    TARGET: {data.case_queue[selectedCaseIdx].title}
                  </div>
                  <div className="grid grid-cols-1 gap-2">
                    <Button 
                      onClick={() => handleMitigate(`Case: ${data.case_queue[selectedCaseIdx].title}`, "Isolate Host")}
                      className="bg-rose-500/20 hover:bg-rose-500/30 text-rose-400 border border-rose-500/30 font-bold uppercase text-[10px] tracking-widest py-5 rounded-xl flex items-center justify-center gap-2 transition-all"
                    >
                      <UserX className="h-4 w-4" /> Isolate Target Host
                    </Button>
                    <Button 
                      onClick={() => handleMitigate(`Case: ${data.case_queue[selectedCaseIdx].title}`, "Block IP Address")}
                      className="bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 border border-amber-500/30 font-bold uppercase text-[10px] tracking-widest py-5 rounded-xl flex items-center justify-center gap-2 transition-all"
                    >
                      <Globe className="h-4 w-4" /> Block Rogue IP Address
                    </Button>
                    <Button 
                      onClick={() => handleMitigate(`Case: ${data.case_queue[selectedCaseIdx].title}`, "Trigger Full Remediation")}
                      className="bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30 font-bold uppercase text-[10px] tracking-widest py-5 rounded-xl flex items-center justify-center gap-2 transition-all"
                    >
                      <FileCheck className="h-4 w-4" /> Trigger Full Remediation
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Incident Tags breakdown */}
          <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
            <CardHeader className="border-b border-border/40 pb-4">
              <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-warning" />
                Threat Vectors Tag Volume
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="h-[180px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={tagChartData} layout="vertical" margin={{ top: 0, right: 10, left: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.1} horizontal={false} />
                    <XAxis type="number" stroke="hsl(var(--muted-foreground))" fontSize={8} tickLine={false} axisLine={false} />
                    <YAxis dataKey="name" type="category" stroke="hsl(var(--muted-foreground))" fontSize={8} width={80} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(0, 0, 0, 0.85)",
                        backdropFilter: "blur(12px)",
                        border: "1px solid hsl(var(--border) / 0.4)",
                        borderRadius: "12px",
                        color: "hsl(var(--foreground))",
                      }}
                    />
                    <Bar dataKey="count" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} barSize={8} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      {/* Confirmation Dialog */}
      <ConfirmActionDialog
        open={!!confirmAction}
        onOpenChange={() => setConfirmAction(null)}
        title={confirmAction?.actionName === "Isolate Host" ? "Isolate Target Host"
          : confirmAction?.actionName === "Block IP Address" ? "Block Rogue IP Address"
          : "Trigger Full Remediation"}
        description={confirmAction?.actionName === "Isolate Host"
          ? "This will disconnect the target host from the network. All active sessions and processes will be terminated. Ensure you have verified the threat."
          : confirmAction?.actionName === "Block IP Address"
          ? "This will block the IP address at the network perimeter. Verify this IP is associated with malicious activity before proceeding."
          : "This will execute the complete remediation playbook, including isolation, IOC blocking, and case closure actions."}
        actionLabel={`Confirm ${confirmAction?.actionName ?? ""}`}
        actionVariant={confirmAction?.actionName === "Isolate Host" ? "destructive" : "warning"}
        targetLabel={confirmAction?.target ?? ""}
        requireReason
        requireTicketId
        onConfirm={executeMitigation}
      />
    </div>
  );
}
