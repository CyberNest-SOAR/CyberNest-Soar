import { useDashboardData } from "@/hooks/useDashboardData";
import { PageHeader } from "@/components/PageHeader";
import { CyberCard } from "@/components/CyberCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  SlidersHorizontal, 
  Workflow, 
  CheckCircle2, 
  RefreshCw, 
  ShieldAlert, 
  Activity, 
  Play,
  Cpu
} from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell } from "recharts";
import { toast } from "sonner";

interface PlaybookLibrary {
  rules: any[];
  default_action: string;
  total_rules: number;
}

interface Outcomes {
  no_action_taken: number;
  false_positive_closed: number;
  unknown: number;
  case_escalated: number;
  automated_block: number;
  automated_quarantine: number;
  ip_blocked: number;
  session_terminated: number;
  password_reset: number;
  manual_review: number;
  ticket_created: number;
}

interface PlaybooksAutomationData {
  page: string;
  playbook_library: PlaybookLibrary;
  execution_history: {
    outcomes: Outcomes;
    total_executions: number;
  };
  simulation_mode: {
    available: boolean;
    endpoint: string;
  };
  approval_workflows: {
    manual_approval_required: any[];
    semi_automated: any[];
    fully_automated: any[];
  };
}

const fallbackDefault: PlaybooksAutomationData = {
  page: "Playbooks & Automation",
  playbook_library: {
    rules: [],
    default_action: "log_event",
    total_rules: 0
  },
  execution_history: {
    outcomes: {
      no_action_taken: 0,
      false_positive_closed: 0,
      unknown: 0,
      case_escalated: 0,
      automated_block: 0,
      automated_quarantine: 0,
      ip_blocked: 0,
      session_terminated: 0,
      password_reset: 0,
      manual_review: 0,
      ticket_created: 0
    },
    total_executions: 0
  },
  simulation_mode: {
    available: false,
    endpoint: ""
  },
  approval_workflows: {
    manual_approval_required: [],
    semi_automated: [],
    fully_automated: []
  }
};

export default function PlaybooksAutomationPage() {
  const { data, loading, refetch } = useDashboardData<PlaybooksAutomationData>("playbooks-automation.json", fallbackDefault);

  const library = data.playbook_library;
  const history = data.execution_history;
  const simulation = data.simulation_mode;

  // Format Recharts playbooks outcomes bar chart data
  const outcomesChartData = Object.entries(history.outcomes || {})
    .map(([key, val]) => ({
      name: key.replace(/_/g, " ").toUpperCase(),
      count: val
    })).sort((a, b) => b.count - a.count);

  const COLORS = [
    "hsl(var(--cyber-blue))",
    "hsl(var(--critical))",
    "hsl(var(--warning))",
    "#a855f7",
    "#ec4899",
    "#eab308",
    "#3b82f6"
  ];

  const handleSimulate = () => {
    toast.success("Simulation Initialized", {
      description: "Evaluating playbook rules engine on test telemetry stream.",
      icon: <Play className="h-4 w-4 text-emerald-500 animate-pulse" />
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
          title="Playbooks & Automation"
          description="SOAR trigger rule evaluations, automated host isolations, block outcomes, and audit histories"
          breadcrumbs={[{ label: "Automation" }, { label: "Playbooks & Automation" }]}
        />
        <div className="flex gap-3 bg-card/40 p-2 rounded-2xl border border-border/40 backdrop-blur-md">
          {simulation.available && (
            <Button variant="outline" size="sm" onClick={handleSimulate} className="font-mono text-xs border-primary/20 bg-primary/5 text-primary flex items-center gap-2 hover:bg-primary/10">
              <Play className="h-3.5 w-3.5 fill-primary" /> Evaluate Simulation
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={refetch} className="font-mono text-xs border-border/40 flex items-center gap-2 hover:bg-primary/5">
            <RefreshCw className="h-3.5 w-3.5" /> Sync Rules
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <CyberCard delay={0.05} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <Workflow className="h-5 w-5" />
            </div>
            <Badge className="bg-primary/10 text-primary border border-primary/20 text-[10px]">EXECUTIONS</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Total Playbook Runs</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-foreground">{history.total_executions?.toLocaleString()}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.1} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500">
              <CheckCircle2 className="h-5 w-5 animate-pulse" />
            </div>
            <Badge variant="outline" className="text-emerald-500 bg-emerald-500/5 border-emerald-500/20 text-[10px]">AUTO_BLOCK</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Automated Block Actions</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-emerald-500">{(history.outcomes?.automated_block + history.outcomes?.ip_blocked)?.toLocaleString()}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.15} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500">
              <ShieldAlert className="h-5 w-5 animate-pulse" />
            </div>
            <Badge variant="outline" className="text-rose-500 bg-rose-500/5 border-rose-500/20 text-[10px]">ESCALATION</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Case Escalations</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-rose-500">{history.outcomes?.case_escalated?.toLocaleString()}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.2} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-500">
              <Cpu className="h-5 w-5" />
            </div>
            <Badge variant="outline" className="text-indigo-400 bg-indigo-500/5 border-indigo-500/20 text-[10px]">SOAR LIBRARY</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Registered SOAR Rules</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-indigo-400">{library.total_rules || 12} Rules</h3>
          </div>
        </CyberCard>
      </div>

      {/* Visualizations outcomes & Workflow cards layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Playbook Outcomes BarChart */}
        <Card className="lg:col-span-2 bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary animate-pulse" />
              SOAR Automated Mitigation Outcomes
            </CardTitle>
            <CardDescription>Breakdown of mitigation outcomes executed by playbook triggers</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={outcomesChartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={7} tickLine={false} axisLine={false} />
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
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} barSize={20}>
                    {outcomesChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Approval Workflows */}
        <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <SlidersHorizontal className="h-4 w-4 text-primary" />
              SOAR Integration Profiles
            </CardTitle>
            <CardDescription>Execution modes configured in playbook engine</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            
            {/* Fully Automated */}
            <div className="p-3.5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 flex justify-between items-center">
              <div>
                <h4 className="font-bold text-xs uppercase text-foreground tracking-wider font-grotesk">Fully Automated</h4>
                <p className="text-[10px] text-muted-foreground/80 font-mono mt-0.5">Auto blocks, quarantine, session terminates</p>
              </div>
              <Badge className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[9px] font-mono">ACTIVE</Badge>
            </div>

            {/* Semi Automated */}
            <div className="p-3.5 rounded-xl border border-amber-500/20 bg-amber-500/5 flex justify-between items-center">
              <div>
                <h4 className="font-bold text-xs uppercase text-foreground tracking-wider font-grotesk">Semi Automated</h4>
                <p className="text-[10px] text-muted-foreground/80 font-mono mt-0.5">Password resets, ticket creations</p>
              </div>
              <Badge className="bg-amber-500/20 text-amber-400 border border-amber-500/30 text-[9px] font-mono">ACTIVE</Badge>
            </div>

            {/* Manual Approval */}
            <div className="p-3.5 rounded-xl border border-primary/20 bg-primary/5 flex justify-between items-center">
              <div>
                <h4 className="font-bold text-xs uppercase text-foreground tracking-wider font-grotesk">Manual Approvals</h4>
                <p className="text-[10px] text-muted-foreground/80 font-mono mt-0.5">Host isolations, network mitigations</p>
              </div>
              <Badge variant="outline" className="text-primary border border-primary/30 text-[9px] font-mono">REQUIRE</Badge>
            </div>

          </CardContent>
        </Card>
      </div>
    </div>
  );
}
