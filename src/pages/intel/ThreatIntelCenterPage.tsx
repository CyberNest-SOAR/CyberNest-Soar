import { useDashboardData } from "@/hooks/useDashboardData";
import { PageHeader } from "@/components/PageHeader";
import { CyberCard } from "@/components/CyberCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { 
  Globe, 
  Database, 
  ShieldCheck, 
  Activity, 
  Compass, 
  Cpu, 
  RefreshCw, 
  Zap
} from "lucide-react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

interface Campaign {
  campaign_id: string;
  events: number;
  attack_types: string[];
  avg_severity: number;
}

interface ThreatIntelData {
  page: string;
  threat_level: string;
  ioc_intelligence: {
    total_unique_ips: number;
    total_unique_domains: number;
    total_unique_hashes: number;
    total_unique_urls: number;
    ioc_sample_ips: string[];
    ioc_sample_domains: string[];
  };
  campaign_intelligence: {
    total_campaigns: number;
    campaigns: Campaign[];
  };
  threat_feed_health: {
    token_usage: Record<string, any>;
    services_configured: number;
    total_iocs_stored: number;
  };
}

const fallbackDefault: ThreatIntelData = {
  page: "Threat Intelligence Center",
  threat_level: "LOW",
  ioc_intelligence: {
    total_unique_ips: 0,
    total_unique_domains: 0,
    total_unique_hashes: 0,
    total_unique_urls: 0,
    ioc_sample_ips: [],
    ioc_sample_domains: []
  },
  campaign_intelligence: {
    total_campaigns: 0,
    campaigns: []
  },
  threat_feed_health: {
    token_usage: {},
    services_configured: 0,
    total_iocs_stored: 0
  }
};

export default function ThreatIntelCenterPage() {
  const { data, loading, refetch } = useDashboardData<ThreatIntelData>("threat-intel-center.json", fallbackDefault);

  const ioc = data.ioc_intelligence;
  const campaign = data.campaign_intelligence;

  // Format Recharts dynamic campaigns volume area chart
  const campaignsChartData = (campaign.campaigns || []).map(c => ({
    name: c.campaign_id.replace("chain-cmp-", "CHAIN-").replace("cmp-", "CMP-").toUpperCase(),
    events: c.events,
    severity: c.avg_severity
  })).slice(0, 8);

  const getThreatLevelBadge = (level: string) => {
    switch (level?.toUpperCase()) {
      case "CRITICAL":
      case "HIGH":
        return "bg-rose-500/20 text-rose-400 border-rose-500/50";
      case "MEDIUM":
        return "bg-amber-500/20 text-amber-400 border-amber-500/50";
      default:
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/50";
    }
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
          title="Threat Intelligence Center"
          description="Inbound global indicators of compromise (IOCs), active Advanced Persistent Threat (APT) campaigns, and feed feeds configuration"
          breadcrumbs={[{ label: "Intel" }, { label: "Threat Intel Center" }]}
        />
        <div className="flex items-center gap-3">
          <Badge className={getThreatLevelBadge(data.threat_level) + " px-4 py-1.5 rounded-xl font-black text-xs"}>
            THREAT LEVEL: {data.threat_level}
          </Badge>
          <Button variant="outline" size="sm" onClick={refetch} className="font-mono text-xs border-border/40 flex items-center gap-2 hover:bg-primary/5">
            <RefreshCw className="h-3.5 w-3.5" /> Force Sync Intel
          </Button>
        </div>
      </div>

      {/* Dynamic Key Indicator Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <CyberCard delay={0.05} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <Globe className="h-5 w-5" />
            </div>
            <Badge className="bg-primary/10 text-primary border border-primary/20 text-[10px]">IPS</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Unique Rogue IPs</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-foreground">{ioc.total_unique_ips} Detections</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.1} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <Database className="h-5 w-5" />
            </div>
            <Badge variant="outline" className="text-purple-400 bg-purple-500/5 border-purple-500/20 text-[10px]">HASHES</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Quarantined Hashes</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-purple-400">{ioc.total_unique_hashes?.toLocaleString()}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.15} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-500">
              <Zap className="h-5 w-5" />
            </div>
            <Badge variant="outline" className="text-amber-500 bg-amber-500/5 border-amber-500/20 text-[10px]">CAMPAIGNS</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">APT Campaigns Tracked</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-amber-400">{campaign.total_campaigns} Active</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.2} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-500">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <Badge variant="outline" className="text-indigo-400 bg-indigo-500/5 border-indigo-500/20 text-[10px]">FEED_HEALTH</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Services Configured</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-indigo-400">{data.threat_feed_health?.services_configured || 4} Feeds</h3>
          </div>
        </CyberCard>
      </div>

      {/* Main Campaign Visualizer and IP table layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Campaign Intelligence AreaChart */}
        <Card className="lg:col-span-2 bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary animate-pulse" />
              APT Campaign Event Volume
            </CardTitle>
            <CardDescription>Event volume analyzed by Advanced Persistent Threat campaign chains</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={campaignsChartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorEvents" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.1} vertical={false} />
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={9} tickLine={false} axisLine={false} />
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
                  <Area type="monotone" dataKey="events" stroke="hsl(var(--primary))" strokeWidth={3} fillOpacity={1} fill="url(#colorEvents)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Unique IOC Sample IP Database */}
        <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <Compass className="h-4 w-4 text-primary" />
              IOC Rogue IP Feeds
            </CardTitle>
            <CardDescription>Logged unique IP addresses tracked in threat campaigns</CardDescription>
          </CardHeader>
          <CardContent className="pt-4 px-0">
            <div className="max-h-[300px] overflow-y-auto custom-scrollbar px-6 space-y-2">
              {(ioc.ioc_sample_ips || []).map((ip, idx) => (
                <div key={idx} className="flex justify-between items-center p-3 rounded-lg border border-border/30 bg-background/20 hover:border-border transition-colors">
                  <span className="font-mono text-xs font-bold text-foreground">{ip}</span>
                  <Badge variant="outline" className="text-[9px] uppercase tracking-wider font-mono bg-rose-500/10 text-rose-400 border-rose-500/35">
                    MALICIOUS
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Campaigns Forensic Table */}
      <Card className="glass border-border/40 shadow-2xl backdrop-blur-md">
        <CardHeader className="border-b border-border/40 pb-4">
          <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
            <Database className="h-4 w-4 text-primary" />
            Active Advanced Persistent Threat Campaigns Registry
          </CardTitle>
          <CardDescription>Technical audit log of threat campaigns, avg severity, and attack vectors detected in the wild</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto max-h-[350px] overflow-y-auto custom-scrollbar">
            <Table>
              <TableHeader>
                <TableRow className="border-border/30 bg-muted/20 hover:bg-transparent">
                  <TableHead className="pl-6 font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Campaign ID</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Event Count</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Average Severity</TableHead>
                  <TableHead className="pr-6 font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Attack Signatures Mapped</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(campaign.campaigns || []).map((c, idx) => (
                  <TableRow key={idx} className="hover:bg-muted/10 border-border/10">
                    <TableCell className="pl-6 font-mono text-xs font-bold text-foreground">
                      {c.campaign_id}
                    </TableCell>
                    <TableCell className="font-mono text-xs font-bold text-muted-foreground">
                      {c.events?.toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={
                        c.avg_severity >= 8 
                          ? "bg-rose-500/10 text-rose-500 border-rose-500/35"
                          : c.avg_severity >= 4 
                          ? "bg-amber-500/10 text-amber-500 border-amber-500/35"
                          : "bg-blue-500/10 text-blue-500 border-blue-500/35"
                      }>
                        Level {c.avg_severity?.toFixed(1)}
                      </Badge>
                    </TableCell>
                    <TableCell className="pr-6">
                      <div className="flex flex-wrap gap-1">
                        {c.attack_types?.slice(0, 6).map((type, tIdx) => (
                          <Badge key={tIdx} variant="outline" className="text-[9px] font-sans bg-background/50 border-border/20 text-muted-foreground">
                            {type.replace("_", " ")}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
