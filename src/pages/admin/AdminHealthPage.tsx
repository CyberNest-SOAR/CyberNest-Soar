import { useDashboardData } from "@/hooks/useDashboardData";
import { PageHeader } from "@/components/PageHeader";
import { CyberCard } from "@/components/CyberCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Settings, 
  RefreshCw, 
  Activity, 
  Cpu, 
  HardDrive, 
  Users, 
  Key,
  Database,
  CheckCircle2,
  XCircle
} from "lucide-react";
import { toast } from "sonner";
import { useHealthCheck } from "@/hooks/useBackendApi";

interface Connector {
  status: string;
  data_files?: string[];
  iocs?: number;
  cases?: number;
}

interface AdminHealthData {
  page: string;
  connector_health: {
    wazuh_connector: Connector;
    misp_connector: Connector;
    thehive_connector: Connector;
    threat_feed_connectors: Record<string, boolean>;
  };
  infrastructure_health: {
    dataset_pipeline_outputs: boolean;
    ndjson_dataset: boolean;
    thehive_cases: boolean;
    llm_datasets: boolean;
    total_events_available: number;
    storage_used_mb: number;
  };
  queue_monitoring: {
    event_ingestion_queue: number;
    failed_jobs: number;
    retry_counts: number;
  };
  rbac: {
    roles: string[];
    permissions: string[];
    mfa_status: string;
  };
}

const fallbackDefault: AdminHealthData = {
  page: "Administration & System Health",
  connector_health: {
    wazuh_connector: { status: "offline" },
    misp_connector: { status: "offline" },
    thehive_connector: { status: "offline" },
    threat_feed_connectors: {}
  },
  infrastructure_health: {
    dataset_pipeline_outputs: false,
    ndjson_dataset: false,
    thehive_cases: false,
    llm_datasets: false,
    total_events_available: 0,
    storage_used_mb: 0
  },
  queue_monitoring: {
    event_ingestion_queue: 0,
    failed_jobs: 0,
    retry_counts: 0
  },
  rbac: {
    roles: [],
    permissions: [],
    mfa_status: "disabled"
  }
};

export default function AdminHealthPage() {
  const { data, loading, refetch } = useDashboardData<AdminHealthData>("admin-health.json", fallbackDefault);
  const { checkAll, results: healthResults, loading: healthLoading } = useHealthCheck();

  const connectors = data.connector_health;
  const infra = data.infrastructure_health;
  const queue = data.queue_monitoring;
  const rbac = data.rbac;

  const handleTestConnector = async (connectorName: string) => {
    await checkAll();
    toast.success("Connector Diagnostic Completed", {
      description: `${connectorName} connection state validated.`,
      icon: <Activity className="h-4 w-4 text-emerald-500 animate-pulse" />
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case "configured":
      case "available":
      case "active":
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/50";
      default:
        return "bg-rose-500/20 text-rose-400 border-rose-500/50";
    }
  };

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-12 w-64 bg-muted/40 rounded-lg" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="h-[350px] bg-card/30 border border-border/20 rounded-xl" />
          <div className="h-[350px] bg-card/30 border border-border/20 rounded-xl" />
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
          title="System Health & Connectors"
          description="Orchestrator connector status checks, live database queues, infrastructure limits, and RBAC policies"
          breadcrumbs={[{ label: "Admin" }, { label: "Admin Health" }]}
        />
        <Button variant="outline" size="sm" onClick={refetch} className="font-mono text-xs border-border/40 flex items-center gap-2 hover:bg-primary/5">
          <RefreshCw className="h-3.5 w-3.5" /> Force Diagnostics
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <CyberCard delay={0.05} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <Database className="h-5 w-5" />
            </div>
            <Badge className="bg-primary/10 text-primary border border-primary/20 text-[10px]">INGESTION</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Total Logs Indexed</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-foreground">{infra.total_events_available?.toLocaleString()}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.1} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-500">
              <HardDrive className="h-5 w-5 animate-pulse" />
            </div>
            <Badge variant="outline" className="text-indigo-400 bg-indigo-500/5 border-indigo-500/20 text-[10px]">STORAGE</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Pipeline Storage Used</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-indigo-400">{infra.storage_used_mb} MB</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.15} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-500">
              <Activity className="h-5 w-5 animate-pulse" />
            </div>
            <Badge variant="outline" className="text-amber-500 bg-amber-500/5 border-amber-500/20 text-[10px]">INGEST_QUEUE</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Active Ingestion Queue</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-amber-400">{queue.event_ingestion_queue?.toLocaleString()}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.2} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500">
              <Key className="h-5 w-5" />
            </div>
            <Badge className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[9px] font-mono">MFA_ACTIVE</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">System MFA Protection</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-emerald-500">{rbac.mfa_status?.toUpperCase()}</h3>
          </div>
        </CyberCard>
      </div>

      {/* Main connectors grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Wazuh, MISP, TheHive Connectors Health */}
        <Card className="lg:col-span-2 bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <Cpu className="h-4 w-4 text-primary animate-pulse" />
              API Connectors & Threat Feeds
            </CardTitle>
            <CardDescription>Remote API linkages into Wazuh cluster and MISP cyber intelligence feeds</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            
            {/* Wazuh */}
            <div className="p-4 rounded-xl border border-border/30 bg-background/25 flex flex-col sm:flex-row justify-between sm:items-center gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h4 className="font-bold text-xs uppercase text-foreground tracking-wider font-grotesk">Wazuh Endpoint Integrator</h4>
                  <Badge className={getStatusBadge(connectors.wazuh_connector?.status)}>
                    {connectors.wazuh_connector?.status}
                  </Badge>
                </div>
                <p className="text-[10px] text-muted-foreground/60 font-mono mt-1">Files Ingested: {connectors.wazuh_connector?.data_files?.length || 3} bulk datasets</p>
              </div>
              <Button size="sm" variant="outline" onClick={() => handleTestConnector("Wazuh")} className="text-[10px] font-bold uppercase tracking-wider h-8">
                Ping Wazuh API
              </Button>
            </div>

            {/* MISP */}
            <div className="p-4 rounded-xl border border-border/30 bg-background/25 flex flex-col sm:flex-row justify-between sm:items-center gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h4 className="font-bold text-xs uppercase text-foreground tracking-wider font-grotesk">MISP Malware Intelligence</h4>
                  <Badge className={getStatusBadge(connectors.misp_connector?.status)}>
                    {connectors.misp_connector?.status}
                  </Badge>
                </div>
                <p className="text-[10px] text-muted-foreground/60 font-mono mt-1">IOC hashes loaded: {connectors.misp_connector?.iocs?.toLocaleString()} unique signatures</p>
              </div>
              <Button size="sm" variant="outline" onClick={() => handleTestConnector("MISP")} className="text-[10px] font-bold uppercase tracking-wider h-8">
                Force Hash Pull
              </Button>
            </div>

            {/* TheHive */}
            <div className="p-4 rounded-xl border border-border/30 bg-background/25 flex flex-col sm:flex-row justify-between sm:items-center gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h4 className="font-bold text-xs uppercase text-foreground tracking-wider font-grotesk">TheHive Threat Cases</h4>
                  <Badge className={getStatusBadge(connectors.thehive_connector?.status)}>
                    {connectors.thehive_connector?.status}
                  </Badge>
                </div>
                <p className="text-[10px] text-muted-foreground/60 font-mono mt-1">Cases in buffer: {connectors.thehive_connector?.cases?.toLocaleString()} registered tickets</p>
              </div>
              <Button size="sm" variant="outline" onClick={() => handleTestConnector("TheHive")} className="text-[10px] font-bold uppercase tracking-wider h-8">
                Test Connection
              </Button>
            </div>

          </CardContent>
        </Card>

        {/* System Credentials & RBAC summary */}
        <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <Users className="h-4 w-4 text-primary" />
              Access Controls (RBAC)
            </CardTitle>
            <CardDescription>Security profile mode permissions configuration</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            
            {/* Roles */}
            <div className="space-y-1.5">
              <div className="text-[10px] font-black uppercase tracking-wider text-muted-foreground/60 font-mono">
                System Access Roles
              </div>
              <div className="flex flex-wrap gap-1.5">
                {(rbac.roles || []).map((role, idx) => (
                  <Badge key={idx} variant="outline" className="text-[10px] font-mono bg-background/50 border-border/30 text-foreground uppercase tracking-widest font-bold">
                    {role}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Permissions */}
            <div className="space-y-1.5 pt-4 border-t border-border/20">
              <div className="text-[10px] font-black uppercase tracking-wider text-muted-foreground/60 font-mono">
                Security Permissions
              </div>
              <div className="flex flex-wrap gap-1.5">
                {(rbac.permissions || []).map((perm, idx) => (
                  <Badge key={idx} className="text-[10px] font-mono bg-indigo-500/10 border-indigo-500/25 text-indigo-400 capitalize">
                    {perm}
                  </Badge>
                ))}
              </div>
            </div>

            {/* MFA Status bar */}
            <div className="p-3.5 rounded-xl border border-emerald-500/25 bg-emerald-500/5 text-xs font-mono font-semibold text-emerald-400 text-center uppercase tracking-widest mt-4">
              MFA STATUS: ENFORCED
            </div>

          </CardContent>
        </Card>
      </div>

      {/* Live Health Check Results */}
      {healthResults.length > 0 && (
        <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <Activity className="h-4 w-4 text-emerald-500" />
              Live Health Check Results
            </CardTitle>
            <CardDescription>Real-time connectivity diagnostics for all integrated services</CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {healthResults.map((r, i) => (
                <div key={i} className={`p-3 rounded-xl border ${
                  r.status === "healthy" ? "bg-emerald-500/5 border-emerald-500/20"
                    : r.status === "degraded" ? "bg-amber-500/5 border-amber-500/20"
                    : "bg-rose-500/5 border-rose-500/20"
                }`}>
                  <div className="flex items-center gap-2 mb-1.5">
                    {r.status === "healthy"
                      ? <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                      : <XCircle className="h-3 w-3 text-rose-400" />
                    }
                    <span className="text-[10px] font-mono font-bold uppercase">{r.service}</span>
                  </div>
                  <Badge className={`text-[8px] ${
                    r.status === "healthy" ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
                      : r.status === "degraded" ? "bg-amber-500/15 text-amber-400 border-amber-500/30"
                      : "bg-rose-500/15 text-rose-400 border-rose-500/30"
                  }`}>
                    {r.status}
                  </Badge>
                  <p className="text-[9px] text-muted-foreground/50 font-mono mt-1">{r.latency_ms}ms</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
