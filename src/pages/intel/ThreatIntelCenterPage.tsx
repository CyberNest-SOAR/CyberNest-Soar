import { useState, useMemo, useCallback } from "react";
import { useDashboardData } from "@/hooks/useDashboardData";
import { PageHeader } from "@/components/PageHeader";
import { CyberCard } from "@/components/CyberCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Globe, Database, ShieldCheck, Activity, Compass, Cpu,
  RefreshCw, Zap, Search, ExternalLink, AlertTriangle, Shield,
  Fingerprint, Layers, Map, Target, Plus, Trash2, Edit3,
  Clock, Wifi, WifiOff, ChevronRight,
} from "lucide-react";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
  BarChart, Bar, Cell, PieChart, Pie,
} from "recharts";
import { toast } from "sonner";
import { IocSearchDialog } from "@/components/IocSearchDialog";
import { Separator } from "@/components/ui/separator";

/* ─── Types ─────────────────────────────────────────────────────────────── */

interface IocItem {
  type: string;
  value: string;
  reputation: string;
  confidence: number;
  source: string;
  first_seen: string;
  last_seen: string;
}

interface IocEnrichment {
  ioc_value: string;
  ioc_type: string;
  virustotal_score: number | null;
  abuseipdb_score: number | null;
  geoip: { country: string; city: string; latitude: number; longitude: number } | null;
  asn: { number: string; name: string } | null;
  whois: { org: string; created: string; abuse_contact: string } | null;
  malware_families: string[];
  threat_categories: string[];
}

interface Campaign {
  campaign_name: string;
  threat_actor: string;
  related_iocs: number;
  mitre_techniques: string[];
  active_cases: number;
  severity: string;
}

interface MitreMapping {
  technique: string;
  name: string;
  tactic: string;
  related_alerts: number;
  related_incidents: number;
}

interface MispEvent {
  event_id: string;
  info: string;
  tags: string[];
  ioc_count: number;
  timestamp: string;
}

interface ThreatFeed {
  name: string;
  status: string;
  last_sync: string;
  ioc_count: number;
  api_health: string;
  rate_limit_remaining: number;
}

interface ThreatIntelData {
  page: string;
  threat_level: string;
  ioc_intelligence: { total_unique_ips: number; total_unique_domains: number; total_unique_hashes: number; total_unique_urls: number; ioc_sample: IocItem[] };
  ioc_enrichment: IocEnrichment[];
  misp_intelligence: { event_count: number; new_iocs_last_24h: number; active_campaigns: number; tags: string[]; tlp_level: string; confidence: number; recent_events: MispEvent[] };
  campaigns: Campaign[];
  mitre_mapping: MitreMapping[];
  threat_feed_health: { services_configured: number; total_iocs_stored: number; feeds: ThreatFeed[] };
}

const fallbackDefault: ThreatIntelData = {
  page: "Threat Intelligence Center",
  threat_level: "LOW",
  ioc_intelligence: { total_unique_ips: 0, total_unique_domains: 0, total_unique_hashes: 0, total_unique_urls: 0, ioc_sample: [] },
  ioc_enrichment: [],
  misp_intelligence: { event_count: 0, new_iocs_last_24h: 0, active_campaigns: 0, tags: [], tlp_level: "AMBER", confidence: 0, recent_events: [] },
  campaigns: [],
  mitre_mapping: [],
  threat_feed_health: { services_configured: 0, total_iocs_stored: 0, feeds: [] },
};

const TOOLTIP_STYLE = {
  backgroundColor: "rgba(11,18,32,0.95)",
  backdropFilter: "blur(12px)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: "12px",
  color: "#f8fafc",
  fontSize: "11px",
};

/* ─── IOC Detail Drawer ──────────────────────────────────────────────────── */

function IocDetailDrawer({ ioc, onClose }: { ioc: IocItem | null; onClose: () => void }) {
  if (!ioc) return null;
  const enrichBadge = (rep: string) => {
    if (rep === "malicious") return "bg-rose-500/15 text-rose-400 border-rose-500/30";
    if (rep === "suspicious") return "bg-amber-500/15 text-amber-400 border-amber-500/30";
    return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-[hsl(var(--background))] border border-border/40 rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/30 bg-primary/5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
              {ioc.type === "ip" ? <Globe className="h-4 w-4" /> : ioc.type === "hash" ? <Fingerprint className="h-4 w-4" /> : <Search className="h-4 w-4" />}
            </div>
            <div>
              <p className="text-[9px] font-mono uppercase tracking-widest text-muted-foreground/50">{ioc.type.toUpperCase()} INTELLIGENCE</p>
              <p className="font-mono font-bold text-sm">{ioc.value}</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8"><span className="text-lg">✕</span></Button>
        </div>
        <div className="px-6 py-4 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-muted/10 rounded-xl p-3 border border-border/20">
              <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50 mb-1">Reputation</p>
              <Badge className={`${enrichBadge(ioc.reputation)} text-[10px] mt-1`}>{ioc.reputation.toUpperCase()}</Badge>
            </div>
            <div className="bg-muted/10 rounded-xl p-3 border border-border/20">
              <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50 mb-1">Confidence</p>
              <p className="text-lg font-black font-mono text-foreground">{(ioc.confidence * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-muted/10 rounded-xl p-3 border border-border/20">
              <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50 mb-1">Source</p>
              <p className="text-sm font-bold font-mono text-foreground/80">{ioc.source}</p>
            </div>
            <div className="bg-muted/10 rounded-xl p-3 border border-border/20">
              <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50 mb-1">First Seen</p>
              <p className="text-sm font-bold font-mono text-foreground/80">{ioc.first_seen}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="text-[10px]" onClick={() => { navigator.clipboard.writeText(ioc.value); toast.success("Copied"); }}>
              Copy IOC
            </Button>
            <Button variant="outline" size="sm" className="text-[10px]" onClick={() => {
              const val = ioc.value;
              const t = ioc.type;
              const url = t === "ip" ? `https://www.virustotal.com/gui/ip-address/${val}`
                : t === "hash" ? `https://www.virustotal.com/gui/file/${val}`
                : t === "domain" ? `https://www.virustotal.com/gui/domain/${val}`
                : `https://www.virustotal.com/gui/search/${val}`;
              window.open(url, "_blank", "noopener,noreferrer");
            }}>
              <ExternalLink className="h-3 w-3 mr-1" /> VT Lookup
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Add Provider Modal ─────────────────────────────────────────────────── */

function AddProviderModal({ open, onClose, onAdd }: { open: boolean; onClose: () => void; onAdd: (p: any) => void }) {
  const [form, setForm] = useState({ name: "", provider_type: "virustotal", api_key: "", base_url: "", rate_limit: "1000", enabled: true });
  if (!open) return null;

  const PROVIDER_TYPES = [
    "virustotal", "abuseipdb", "alienvault_otx", "misp", "opencit",
    "greynoise", "urlhaus", "hybridanalysis", "custom",
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-[hsl(var(--background))] border border-border/40 rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="px-6 py-4 border-b border-border/30">
          <h3 className="text-lg font-bold">+ Add Threat Feed</h3>
          <p className="text-xs text-muted-foreground/60">Connect a new threat intelligence provider</p>
        </div>
        <div className="px-6 py-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Provider Name</label>
              <Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="My Threat Feed" className="bg-background/50 border-border/30 text-xs" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Provider Type</label>
              <select value={form.provider_type} onChange={e => setForm({ ...form, provider_type: e.target.value })}
                className="w-full bg-background/50 border border-border/30 text-xs px-3 py-2 rounded-lg text-foreground focus:ring-1 focus:ring-primary outline-none">
                {PROVIDER_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, " ").toUpperCase()}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">API Key</label>
              <Input value={form.api_key} onChange={e => setForm({ ...form, api_key: e.target.value })} placeholder="sk-..." type="password" className="bg-background/50 border-border/30 text-xs" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Base URL</label>
              <Input value={form.base_url} onChange={e => setForm({ ...form, base_url: e.target.value })} placeholder="https://api.provider.com" className="bg-background/50 border-border/30 text-xs" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Rate Limit (req/min)</label>
              <Input value={form.rate_limit} onChange={e => setForm({ ...form, rate_limit: e.target.value })} placeholder="1000" className="bg-background/50 border-border/30 text-xs" />
            </div>
            <div className="space-y-2 flex items-end pb-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={form.enabled} onChange={e => setForm({ ...form, enabled: e.target.checked })}
                  className="rounded border-border/40 bg-background/50" />
                <span className="text-xs font-medium">Enabled on creation</span>
              </label>
            </div>
          </div>
        </div>
        <div className="px-6 py-4 border-t border-border/30 flex justify-end gap-3">
          <Button variant="outline" size="sm" onClick={onClose}>Cancel</Button>
          <Button size="sm" onClick={() => { onAdd(form); onClose(); }} disabled={!form.name || !form.api_key}>
            <Plus className="h-3.5 w-3.5 mr-1.5" /> Add Provider
          </Button>
        </div>
      </div>
    </div>
  );
}

/* ─── Main Page ──────────────────────────────────────────────────────────── */

export default function ThreatIntelCenterPage() {
  const { data, loading, refetch } = useDashboardData<ThreatIntelData>("threat-intel-center.json", fallbackDefault);

  const [selectedIoc, setSelectedIoc] = useState<string | null>(null);
  const [selectedIocType, setSelectedIocType] = useState<"ip" | "domain" | "hash" | "url">("ip");
  const [selectedIocDetail, setSelectedIocDetail] = useState<IocItem | null>(null);
  const [showAddProvider, setShowAddProvider] = useState(false);
  const [feeds, setFeeds] = useState<ThreatFeed[]>(data?.threat_feed_health?.feeds ?? []);

  const ioc = data.ioc_intelligence;
  const enrichment = data.ioc_enrichment ?? [];
  const misp = data.misp_intelligence;
  const campaigns = data.campaigns ?? [];
  const mitre = data.mitre_mapping ?? [];

  const searchIoc = (value: string, type: "ip" | "domain" | "hash" | "url") => {
    setSelectedIoc(value);
    setSelectedIocType(type);
  };

  const getReputationBadge = (rep: string) => {
    switch (rep) {
      case "malicious": return "bg-rose-500/15 text-rose-400 border-rose-500/30";
      case "suspicious": return "bg-amber-500/15 text-amber-400 border-amber-500/30";
      default: return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    }
  };

  const getThreatLevelBadge = (level: string) => {
    switch (level?.toUpperCase()) {
      case "CRITICAL": return "bg-rose-500/20 text-rose-400 border-rose-500/50";
      case "HIGH": return "bg-orange-500/20 text-orange-400 border-orange-500/50";
      case "MEDIUM": return "bg-amber-500/20 text-amber-400 border-amber-500/50";
      default: return "bg-emerald-500/20 text-emerald-400 border-emerald-500/50";
    }
  };

  const addProvider = (p: any) => {
    const newFeed: ThreatFeed = {
      name: p.name,
      status: p.enabled ? "active" : "inactive",
      last_sync: new Date().toISOString(),
      ioc_count: 0,
      api_health: "healthy",
      rate_limit_remaining: parseInt(p.rate_limit),
    };
    setFeeds(prev => [newFeed, ...prev]);
    toast.success("Provider Added", { description: `${p.name} connected successfully.` });
  };

  const removeFeed = (name: string) => {
    setFeeds(prev => prev.filter(f => f.name !== name));
    toast.success("Provider Removed", { description: `${name} disconnected.` });
  };

  const [selectedTechnique, setSelectedTechnique] = useState<string | null>(null);
  const [hoveredTech, setHoveredTech] = useState<MitreMapping | null>(null);

  const tacticGroups = useMemo(() => {
    const groups: Record<string, MitreMapping[]> = {};
    mitre.forEach(m => {
      if (!groups[m.tactic]) groups[m.tactic] = [];
      groups[m.tactic].push(m);
    });
    return groups;
  }, [mitre]);

  const maxAlerts = Math.max(...mitre.map(m => m.related_alerts), 1);

  const matrixCellSize = 48;
  const matrixGap = 4;

  const getMatrixColor = useCallback((alerts: number) => {
    const ratio = Math.log(alerts + 1) / Math.log(maxAlerts + 1);
    if (ratio > 0.7) return "rgba(239,68,68,0.6)";
    if (ratio > 0.4) return "rgba(251,191,36,0.5)";
    if (ratio > 0.15) return "rgba(168,85,247,0.4)";
    return "rgba(100,116,139,0.25)";
  }, [maxAlerts]);

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-12 w-64 bg-muted/40 rounded-lg" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-[350px] bg-card/30 border border-border/20 rounded-xl" />
          <div className="h-[350px] bg-card/3 border border-border/20 rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <PageHeader
          title="Threat Intelligence Center"
          description="External threat intelligence: IOC analysis, enrichment, campaigns, and MITRE ATT&CK mapping"
          breadcrumbs={[{ label: "Intel" }, { label: "Threat Intel Center" }]}
        />
        <div className="flex items-center gap-3">
          <Badge className={getThreatLevelBadge(data.threat_level) + " px-4 py-1.5 rounded-xl font-black text-xs"}>
            THREAT LEVEL: {data.threat_level}
          </Badge>
          <Button variant="outline" size="sm" onClick={refetch} className="font-mono text-xs border-border/40 flex items-center gap-2 hover:bg-primary/5">
            <RefreshCw className="h-3.5 w-3.5" /> Sync Intel
          </Button>
        </div>
      </div>

      {/* Top KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <CyberCard delay={0.05} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-3"><div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary"><Globe className="h-5 w-5" /></div><Badge className="bg-primary/10 text-primary border-primary/20 text-[10px]">IPS</Badge></div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Unique IPs</p>
          <h3 className="text-2xl font-black font-mono">{ioc.total_unique_ips.toLocaleString()}</h3>
        </CyberCard>
        <CyberCard delay={0.1} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-3"><div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400"><Fingerprint className="h-5 w-5" /></div><Badge variant="outline" className="text-purple-400 bg-purple-500/5 border-purple-500/20 text-[10px]">HASHES</Badge></div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Quarantined Hashes</p>
          <h3 className="text-2xl font-black font-mono text-purple-400">{ioc.total_unique_hashes?.toLocaleString()}</h3>
        </CyberCard>
        <CyberCard delay={0.15} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-3"><div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-500"><Target className="h-5 w-5" /></div><Badge variant="outline" className="text-amber-500 bg-amber-500/5 border-amber-500/20 text-[10px]">CAMPAIGNS</Badge></div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Active Campaigns</p>
          <h3 className="text-2xl font-black font-mono text-amber-400">{campaigns.length} Active</h3>
        </CyberCard>
        <CyberCard delay={0.2} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-3"><div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-500"><ShieldCheck className="h-5 w-5" /></div><Badge variant="outline" className="text-indigo-400 bg-indigo-500/5 border-indigo-500/20 text-[10px]">IOCS</Badge></div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Total IOCs Stored</p>
          <h3 className="text-2xl font-black font-mono text-indigo-400">{(data.threat_feed_health?.total_iocs_stored ?? 0).toLocaleString()}</h3>
        </CyberCard>
      </div>

      {/* Tabs: Threat Intelligence Data | Threat Feed Management */}
      <Tabs defaultValue="intel-data" className="w-full">
        <TabsList className="bg-muted/20 border border-border/30 p-1">
          <TabsTrigger value="intel-data" className="text-xs data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
            <Globe className="h-3.5 w-3.5 mr-1.5" /> Threat Intelligence Data
          </TabsTrigger>
          <TabsTrigger value="feed-mgmt" className="text-xs data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
            <Wifi className="h-3.5 w-3.5 mr-1.5" /> Threat Feed Management
          </TabsTrigger>
        </TabsList>

        {/* ═══ TAB 1: THREAT INTELLIGENCE DATA ═══ */}
        <TabsContent value="intel-data" className="space-y-8 mt-6">
          {/* IOC Intelligence + MISP row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* IOC Intelligence Table */}
            <Card className="lg:col-span-2 bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
              <CardHeader className="border-b border-border/40 pb-4">
                <CardTitle className="text-lg font-bold flex items-center gap-2">
                  <Database className="h-4 w-4 text-primary" />
                  IOC Intelligence
                </CardTitle>
                <CardDescription>Indicators of Compromise with reputation, confidence, and source attribution</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <div className="max-h-[350px] overflow-y-auto custom-scrollbar">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-border/20 bg-muted/10 hover:bg-transparent">
                        <TableHead className="pl-4 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Type</TableHead>
                        <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Value</TableHead>
                        <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Reputation</TableHead>
                        <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Source</TableHead>
                        <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Confidence</TableHead>
                        <TableHead className="pr-4 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Last Seen</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(ioc.ioc_sample ?? []).map((item, idx) => (
                        <TableRow key={idx} className="hover:bg-muted/10 border-border/10 cursor-pointer"
                          onClick={() => setSelectedIocDetail(item)}>
                          <TableCell className="pl-4">
                            <Badge variant="outline" className="text-[9px] font-mono bg-background/30 border-border/20">
                              {item.type.toUpperCase()}
                            </Badge>
                          </TableCell>
                          <TableCell className="font-mono text-xs font-bold text-foreground/80 max-w-[180px] truncate">
                            {item.value}
                          </TableCell>
                          <TableCell>
                            <Badge className={`${getReputationBadge(item.reputation)} text-[9px]`}>{item.reputation.toUpperCase()}</Badge>
                          </TableCell>
                          <TableCell className="font-mono text-[10px] text-muted-foreground/70">{item.source}</TableCell>
                          <TableCell>
                            <span className={`font-mono text-xs font-bold ${item.confidence >= 0.9 ? "text-emerald-400" : item.confidence >= 0.7 ? "text-amber-400" : "text-muted-foreground"}`}>
                              {(item.confidence * 100).toFixed(0)}%
                            </span>
                          </TableCell>
                          <TableCell className="pr-4 font-mono text-[10px] text-muted-foreground/50">{item.last_seen}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>

            {/* MISP Intelligence */}
            <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
              <CardHeader className="border-b border-border/40 pb-4">
                <CardTitle className="text-lg font-bold flex items-center gap-2">
                  <Layers className="h-4 w-4 text-violet-400" />
                  MISP Intelligence
                </CardTitle>
                <CardDescription>Malware Information Sharing Platform events</CardDescription>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: "Events", value: misp.event_count.toLocaleString(), color: "text-violet-400" },
                    { label: "New IOCs (24h)", value: misp.new_iocs_last_24h.toLocaleString(), color: "text-sky-400" },
                    { label: "Active Campaigns", value: misp.active_campaigns.toString(), color: "text-amber-400" },
                    { label: "Confidence", value: `${(misp.confidence * 100).toFixed(0)}%`, color: "text-emerald-400" },
                  ].map(s => (
                    <div key={s.label} className="bg-muted/10 rounded-xl p-3 border border-border/20">
                      <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50 mb-1">{s.label}</p>
                      <p className={`text-lg font-black font-mono ${s.color}`}>{s.value}</p>
                    </div>
                  ))}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {misp.tags.map((t, i) => (
                    <Badge key={i} variant="outline" className="text-[9px] bg-violet-500/5 border-violet-500/20 text-violet-400">{t}</Badge>
                  ))}
                </div>
                <div>
                  <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50 mb-2">Latest Events</p>
                  <div className="space-y-1.5">
                    {(misp.recent_events ?? []).slice(0, 3).map((ev, i) => (
                      <div key={i} className="bg-muted/10 rounded-lg p-2.5 border border-border/20">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[9px] font-mono font-bold text-violet-400/80">{ev.event_id}</span>
                          <span className="text-[9px] font-mono text-muted-foreground/40">{ev.ioc_count} IOCs</span>
                        </div>
                        <p className="text-[10px] text-foreground/60 line-clamp-2">{ev.info}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* IOC Enrichment */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Shield className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-bold">IOC Enrichment</h2>
              <p className="text-xs text-muted-foreground/60 ml-auto">Multi-source enrichment: VT, AbuseIPDB, GeoIP, ASN, WHOIS</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {enrichment.slice(0, 3).map((item, idx) => (
                <div key={item.ioc_value} className="rounded-2xl border border-border/30 bg-card/20 backdrop-blur-md p-5 hover:bg-card/30 transition-all">
                  <div className="flex items-center gap-2 mb-3">
                    <Badge variant="outline" className="text-[9px] font-mono">{item.ioc_type.toUpperCase()}</Badge>
                    <span className="font-mono text-xs font-bold text-foreground/80 truncate">{item.ioc_value}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 mb-3">
                    {item.virustotal_score !== null && (
                      <div className="bg-muted/10 rounded-lg p-2 border border-border/20">
                        <p className="text-[8px] uppercase tracking-widest text-muted-foreground/50">VT Score</p>
                        <p className="text-sm font-bold font-mono" style={{ color: item.virustotal_score >= 80 ? COLORS.rose : item.virustotal_score >= 50 ? COLORS.amber : COLORS.emerald }}>{item.virustotal_score}</p>
                      </div>
                    )}
                    {item.abuseipdb_score !== null && (
                      <div className="bg-muted/10 rounded-lg p-2 border border-border/20">
                        <p className="text-[8px] uppercase tracking-widest text-muted-foreground/50">AbuseIPDB</p>
                        <p className="text-sm font-bold font-mono" style={{ color: item.abuseipdb_score >= 80 ? COLORS.rose : item.abuseipdb_score >= 50 ? COLORS.amber : COLORS.emerald }}>{item.abuseipdb_score}</p>
                      </div>
                    )}
                    {item.geoip && (
                      <div className="bg-muted/10 rounded-lg p-2 border border-border/20">
                        <p className="text-[8px] uppercase tracking-widest text-muted-foreground/50">GeoIP</p>
                        <p className="text-[10px] font-bold font-mono text-foreground/70">{item.geoip.country}, {item.geoip.city}</p>
                      </div>
                    )}
                    {item.asn && (
                      <div className="bg-muted/10 rounded-lg p-2 border border-border/20">
                        <p className="text-[8px] uppercase tracking-widest text-muted-foreground/50">ASN</p>
                        <p className="text-[9px] font-bold font-mono text-foreground/70 truncate">{item.asn.name}</p>
                      </div>
                    )}
                  </div>
                  {item.malware_families.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {item.malware_families.map((f, i) => (
                        <Badge key={i} className="bg-rose-500/10 text-rose-400 border-rose-500/20 text-[8px]">{f}</Badge>
                      ))}
                    </div>
                  )}
                  {item.threat_categories.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {item.threat_categories.map((c, i) => (
                        <Badge key={i} variant="outline" className="text-[8px] bg-amber-500/5 border-amber-500/20 text-amber-400">{c}</Badge>
                      ))}
                    </div>
                  )}
                  <Button variant="outline" size="sm" onClick={() => searchIoc(item.ioc_value, item.ioc_type as "ip" | "domain" | "hash" | "url")} className="w-full mt-2 text-[9px] h-7 gap-1.5">
                    <Search className="h-3 w-3" /> Deep Lookup
                  </Button>
                </div>
              ))}
            </div>
          </div>

          {/* Campaign Tracking */}
          <Card className="glass border-border/40 shadow-2xl backdrop-blur-md">
            <CardHeader className="border-b border-border/40 pb-4">
              <CardTitle className="text-lg font-bold flex items-center gap-2">
                <Target className="h-4 w-4 text-amber-400" />
                Campaign Tracking
              </CardTitle>
              <CardDescription>Active threat campaigns with actor attribution, MITRE techniques, and case counts</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto max-h-[350px] overflow-y-auto custom-scrollbar">
                <Table>
                  <TableHeader>
                    <TableRow className="border-border/20 bg-muted/10 hover:bg-transparent">
                      <TableHead className="pl-4 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Campaign</TableHead>
                      <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Threat Actor</TableHead>
                      <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">IOCs</TableHead>
                      <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">MITRE Techniques</TableHead>
                      <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Cases</TableHead>
                      <TableHead className="pr-4 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Severity</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {campaigns.map((c, idx) => (
                      <TableRow key={c.campaign_name} className="hover:bg-muted/10 border-border/10">
                        <TableCell className="pl-4 font-mono text-xs font-bold text-foreground">{c.campaign_name}</TableCell>
                        <TableCell className="font-mono text-xs text-muted-foreground/80">{c.threat_actor}</TableCell>
                        <TableCell className="font-mono text-xs font-bold text-muted-foreground">{c.related_iocs.toLocaleString()}</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {c.mitre_techniques.slice(0, 3).map((t, i) => (
                              <Badge key={i} variant="outline" className="text-[8px] bg-primary/5 border-primary/20 text-primary/70 font-mono">{t}</Badge>
                            ))}
                            {c.mitre_techniques.length > 3 && (
                              <span className="text-[8px] text-muted-foreground/40 font-mono">+{c.mitre_techniques.length - 3}</span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="font-mono text-xs font-bold text-muted-foreground">{c.active_cases}</TableCell>
                        <TableCell className="pr-4">
                          <Badge className={
                            c.severity === "critical" ? "bg-rose-500/15 text-rose-400 border-rose-500/30 text-[9px]" :
                            c.severity === "high" ? "bg-orange-500/15 text-orange-400 border-orange-500/30 text-[9px]" :
                            "bg-amber-500/15 text-amber-400 border-amber-500/30 text-[9px]"
                          }>
                            {c.severity.toUpperCase()}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* MITRE ATT&CK Mapping */}
          <Card className="glass border-border/40 shadow-2xl backdrop-blur-md">
            <CardHeader className="border-b border-border/40 pb-4 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg font-bold flex items-center gap-2">
                  <Map className="h-4 w-4 text-primary" />
                  MITRE ATT&CK Matrix
                </CardTitle>
                <CardDescription>Interactive technique-to-tactic mapping — hover for details, click to filter table</CardDescription>
              </div>
              {selectedTechnique && (
                <Button variant="ghost" size="sm" onClick={() => setSelectedTechnique(null)}
                  className="text-[10px] text-muted-foreground/50 hover:text-foreground">
                  Clear filter
                </Button>
              )}
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* SVG Attack Matrix */}
                <div className="overflow-x-auto custom-scrollbar">
                  {Object.keys(tacticGroups).length === 0 ? (
                    <div className="h-40 flex items-center justify-center text-muted-foreground/40 font-mono text-xs">
                      No MITRE techniques mapped
                    </div>
                  ) : (
                    <svg width={Object.keys(tacticGroups).length * (matrixCellSize + matrixGap) + 20} height="240" className="mx-auto">
                      {Object.entries(tacticGroups).map(([tactic, techniques], colIdx) => {
                        const colX = colIdx * (matrixCellSize + matrixGap) + 10;
                        return (
                          <g key={tactic}>
                            <text x={colX + matrixCellSize / 2} y={14} textAnchor="middle"
                              className="fill-muted-foreground/50"
                              fontSize="7" fontFamily="monospace" fontWeight="800" textLength={matrixCellSize + 4} lengthAdjust="spacingAndGlyphs">
                              {tactic.replace(/\s/g, "\u00A0")}
                            </text>
                            {techniques.map((m, rowIdx) => {
                              const cy = 28 + rowIdx * (matrixCellSize + matrixGap);
                              const isSelected = selectedTechnique === m.technique;
                              return (
                                <g key={m.technique} className="cursor-pointer"
                                  onMouseEnter={() => setHoveredTech(m)}
                                  onMouseLeave={() => setHoveredTech(null)}
                                  onClick={() => setSelectedTechnique(selectedTechnique === m.technique ? null : m.technique)}>
                                  <rect x={colX + 2} y={cy + 2} width={matrixCellSize - 4} height={matrixCellSize - 4} rx={6}
                                    fill={getMatrixColor(m.related_alerts)}
                                    stroke={isSelected ? "rgba(168,85,247,0.9)" : "rgba(255,255,255,0.08)"}
                                    strokeWidth={isSelected ? 2 : 0.5}
                                    className="transition-all duration-150 hover:brightness-125"
                                  />
                                  <text x={colX + matrixCellSize / 2} y={cy + matrixCellSize / 2 + 2} textAnchor="middle"
                                    className="fill-muted-foreground/60" fontSize="6" fontFamily="monospace" fontWeight="600">
                                    {m.technique.substring(0, 8)}
                                  </text>
                                  <text x={colX + matrixCellSize / 2} y={cy + matrixCellSize - 6} textAnchor="middle"
                                    className="fill-foreground/40" fontSize="7" fontFamily="monospace" fontWeight="700">
                                    {m.related_alerts}
                                  </text>
                                </g>
                              );
                            })}
                          </g>
                        );
                      })}
                    </svg>
                  )}
                  {hoveredTech && (
                    <div className="flex items-center justify-center gap-4 mt-2 text-[10px] font-mono bg-card/40 border border-border/20 rounded-lg px-3 py-1.5 mx-auto w-fit">
                      <span className="text-primary font-bold">{hoveredTech.technique}</span>
                      <span className="text-foreground/70">{hoveredTech.name}</span>
                      <span className="text-muted-foreground/50">|</span>
                      <span className="text-foreground/60">Alerts: <strong className="text-amber-400">{hoveredTech.related_alerts.toLocaleString()}</strong></span>
                      <span className="text-foreground/60">Incidents: <strong className="text-violet-400">{hoveredTech.related_incidents.toLocaleString()}</strong></span>
                    </div>
                  )}
                </div>
                {/* Technique Detail Table */}
                <div className="overflow-x-auto max-h-[260px] overflow-y-auto custom-scrollbar">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-border/20 bg-muted/10 hover:bg-transparent">
                        <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Technique</TableHead>
                        <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Name</TableHead>
                        <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Tactic</TableHead>
                        <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Alerts</TableHead>
                        <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Incidents</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(selectedTechnique ? mitre.filter(m => m.technique === selectedTechnique) : mitre).map((m, idx) => (
                        <TableRow key={m.technique} className={`hover:bg-muted/10 border-border/10 ${selectedTechnique === m.technique ? "bg-primary/5" : ""}`}>
                          <TableCell className="font-mono text-[10px] font-bold text-primary/80">{m.technique}</TableCell>
                          <TableCell className="text-xs text-foreground/70">{m.name}</TableCell>
                          <TableCell><Badge variant="outline" className="text-[8px] bg-primary/5 border-primary/20 text-primary/70">{m.tactic}</Badge></TableCell>
                          <TableCell className="font-mono text-xs font-bold text-muted-foreground">{m.related_alerts.toLocaleString()}</TableCell>
                          <TableCell className="font-mono text-xs font-bold text-muted-foreground">{m.related_incidents.toLocaleString()}</TableCell>
                        </TableRow>
                      ))}
                      {selectedTechnique && mitre.filter(m => m.technique === selectedTechnique).length === 0 && (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center py-8 text-muted-foreground/40 font-mono text-xs">
                            No matching technique
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ═══ TAB 2: THREAT FEED MANAGEMENT ═══ */}
        <TabsContent value="feed-mgmt" className="space-y-6 mt-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold flex items-center gap-2">
                <Wifi className="h-5 w-5 text-primary" />
                Connected Providers
              </h2>
              <p className="text-xs text-muted-foreground/60">Manage threat intelligence provider connections</p>
            </div>
            <Button size="sm" onClick={() => setShowAddProvider(true)}>
              <Plus className="h-4 w-4 mr-1.5" /> Add Threat Feed
            </Button>
          </div>

          <Card className="glass border-border/40 shadow-xl backdrop-blur-md overflow-hidden">
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="border-border/20 bg-muted/10 hover:bg-transparent">
                    <TableHead className="pl-6 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Provider</TableHead>
                    <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Status</TableHead>
                    <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">API Health</TableHead>
                    <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Last Sync</TableHead>
                    <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">IOC Count</TableHead>
                    <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Rate Limit</TableHead>
                    <TableHead className="pr-6 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(feeds.length > 0 ? feeds : data.threat_feed_health?.feeds ?? []).map((feed, idx) => (
                    <TableRow key={feed.name} className="hover:bg-muted/10 border-border/10">
                      <TableCell className="pl-6 font-mono text-xs font-bold text-foreground">{feed.name}</TableCell>
                      <TableCell>
                        <Badge className={
                          feed.status === "active" ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30 text-[9px] gap-1" :
                          "bg-muted/30 text-muted-foreground border-border/30 text-[9px] gap-1"
                        }>
                          {feed.status === "active" ? <Wifi className="h-2.5 w-2.5" /> : <WifiOff className="h-2.5 w-2.5" />}
                          {feed.status.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={
                          feed.api_health === "healthy" ? "text-emerald-400 border-emerald-500/20 text-[9px]" :
                          feed.api_health === "degraded" ? "text-amber-400 border-amber-500/20 text-[9px]" :
                          "text-rose-400 border-rose-500/20 text-[9px]"
                        }>
                          {feed.api_health.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-[10px] text-muted-foreground/60">
                        {new Date(feed.last_sync).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </TableCell>
                      <TableCell className="font-mono text-xs font-bold text-muted-foreground">{feed.ioc_count.toLocaleString()}</TableCell>
                      <TableCell className="font-mono text-[10px] text-muted-foreground/60">{feed.rate_limit_remaining.toLocaleString()} / min</TableCell>
                      <TableCell className="pr-6">
                        <div className="flex gap-1">
                          <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => toast.success("Sync triggered", { description: `${feed.name} sync initiated.` })}>
                            <RefreshCw className="h-3 w-3" />
                          </Button>
                          <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-rose-400 hover:text-rose-300" onClick={() => removeFeed(feed.name)}>
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-card/20 border-border/40">
              <CardHeader className="pb-2"><CardTitle className="text-sm font-bold flex items-center gap-2"><Activity className="h-4 w-4 text-primary" /> Rate Limits</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {(feeds.length > 0 ? feeds : data.threat_feed_health?.feeds ?? []).map(f => (
                  <div key={f.name} className="flex items-center justify-between text-[10px]">
                    <span className="font-mono font-bold text-muted-foreground/80">{f.name}</span>
                    <span className="font-mono text-muted-foreground/60">{f.rate_limit_remaining.toLocaleString()} / min</span>
                  </div>
                ))}
              </CardContent>
            </Card>
            <Card className="bg-card/20 border-border/40">
              <CardHeader className="pb-2"><CardTitle className="text-sm font-bold flex items-center gap-2"><Clock className="h-4 w-4 text-primary" /> Sync History</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {(feeds.length > 0 ? feeds : data.threat_feed_health?.feeds ?? []).slice(0, 4).map(f => (
                  <div key={f.name} className="flex items-center justify-between text-[10px]">
                    <span className="font-mono font-bold text-muted-foreground/80">{f.name}</span>
                    <span className="font-mono text-muted-foreground/60">{new Date(f.last_sync).toLocaleString()}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
            <Card className="bg-card/20 border-border/40">
              <CardHeader className="pb-2"><CardTitle className="text-sm font-bold flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-primary" /> Health Checks</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {(feeds.length > 0 ? feeds : data.threat_feed_health?.feeds ?? []).map(f => (
                  <div key={f.name} className="flex items-center justify-between text-[10px]">
                    <span className="font-mono font-bold text-muted-foreground/80">{f.name}</span>
                    <Badge variant="outline" className={`text-[8px] ${f.api_health === "healthy" ? "text-emerald-400" : "text-amber-400"}`}>{f.api_health.toUpperCase()}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* IOC Search Dialog */}
      <IocSearchDialog
        open={!!selectedIoc}
        onOpenChange={() => setSelectedIoc(null)}
        ioc={selectedIoc ?? ""}
        iocType={selectedIocType}
      />

      {/* IOC Detail Drawer */}
      {selectedIocDetail && (
        <IocDetailDrawer ioc={selectedIocDetail} onClose={() => setSelectedIocDetail(null)} />
      )}

      {/* Add Provider Modal */}
      <AddProviderModal open={showAddProvider} onClose={() => setShowAddProvider(false)} onAdd={addProvider} />
    </div>
  );
}

const COLORS = {
  emerald: "#10b981",
  rose: "#f43f5e",
  amber: "#f59e0b",
  orange: "#f97316",
  sky: "#22d3ee",
  violet: "#8b5cf6",
  indigo: "#6366f1",
  purple: "#a855f7",
  cyan: "#06b6d4",
};
