import { useState, useMemo } from "react";
import { useDashboardData } from "@/hooks/useDashboardData";
import { PageHeader } from "@/components/PageHeader";
import { CyberCard } from "@/components/CyberCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { 
  Monitor, 
  Search, 
  Filter, 
  Activity, 
  ShieldCheck, 
  Users, 
  Cpu, 
  RefreshCw,
  Info,
  ServerCrash
} from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell } from "recharts";
import { toast } from "sonner";

interface Asset {
  ip: string;
  hostname: string;
  os_version: string;
  criticality: string;
  host_role: string;
  department: string;
  business_unit: string;
  total_alerts: number;
  unique_processes: string[];
  unique_users: string[];
  attack_types: string[];
  avg_severity: number;
  max_severity: number;
  suppression_rate: number;
}

interface AssetIntelligenceData {
  page: string;
  asset_inventory: Asset[];
  stats: {
    total_assets: number;
    high_criticality: number;
    medium_criticality: number;
    low_criticality: number;
    avg_asset_severity: number;
  };
  remediation_actions: string[];
}

const fallbackDefault: AssetIntelligenceData = {
  page: "Asset & Endpoint Intelligence",
  asset_inventory: [],
  stats: {
    total_assets: 0,
    high_criticality: 0,
    medium_criticality: 0,
    low_criticality: 0,
    avg_asset_severity: 0
  },
  remediation_actions: []
};

export default function AssetIntelligencePage() {
  const { data, loading, refetch } = useDashboardData<AssetIntelligenceData>("asset-intelligence.json", fallbackDefault);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedAssetIdx, setSelectedAssetIdx] = useState<number | null>(null);
  const [criticalityFilter, setCriticalityFilter] = useState("all");

  const stats = data.stats;

  const criticalityData = [
    { name: "CRITICAL", count: stats.high_criticality, fill: "hsl(var(--critical))" },
    { name: "MEDIUM", count: stats.medium_criticality, fill: "hsl(var(--warning))" },
    { name: "LOW", count: stats.low_criticality, fill: "hsl(var(--cyber-blue))" }
  ];

  const handleAction = (ip: string, actionName: string) => {
    toast.success("Command Executed", {
      description: `Action '${actionName}' executed successfully on target ${ip}`,
      icon: <Cpu className="h-4 w-4 text-primary animate-spin" />
    });
  };

  const getCriticalityBadge = (criticality: string) => {
    switch (criticality?.toLowerCase()) {
      case "critical":
        return "bg-rose-500/20 text-rose-400 border-rose-500/50";
      case "high":
        return "bg-orange-500/20 text-orange-400 border-orange-500/50";
      case "medium":
        return "bg-amber-500/20 text-amber-400 border-amber-500/50";
      default:
        return "bg-blue-500/20 text-blue-400 border-blue-500/50";
    }
  };

  // Filter logic
  const filteredAssets = useMemo(() => {
    return (data.asset_inventory || []).filter(asset => {
      const matchesSearch = 
        asset.hostname?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        asset.ip?.includes(searchTerm) ||
        asset.host_role?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        asset.department?.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesCriticality = criticalityFilter === "all" || asset.criticality === criticalityFilter;

      return matchesSearch && matchesCriticality;
    });
  }, [data.asset_inventory, searchTerm, criticalityFilter]);

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
          title="Asset & Endpoint Intelligence"
          description="Consolidated host inventory database, criticality levels, active processes, and user sessions"
          breadcrumbs={[{ label: "Assets" }, { label: "Asset Intelligence" }]}
        />
        <Button variant="outline" size="sm" onClick={refetch} className="font-mono text-xs border-border/40 flex items-center gap-2 hover:bg-primary/5">
          <RefreshCw className="h-3.5 w-3.5" /> Sync Inventory
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <CyberCard delay={0.05} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <Monitor className="h-5 w-5" />
            </div>
            <Badge className="bg-primary/10 text-primary border border-primary/20 text-[10px]">INVENTORY</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Total Active Nodes</p>
            <h3 className="text-3xl font-black font-mono tracking-tight">{stats.total_assets}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.1} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500">
              <ServerCrash className="h-5 w-5 animate-pulse" />
            </div>
            <Badge variant="outline" className="text-rose-500 bg-rose-500/5 border-rose-500/20 text-[10px]">CRITICAL</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">High Criticality Assets</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-rose-500">{stats.high_criticality}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.15} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-yellow-500/10 border border-yellow-500/20 text-yellow-500">
              <Activity className="h-5 w-5 animate-pulse" />
            </div>
            <Badge variant="outline" className="text-yellow-500 bg-yellow-500/5 border-yellow-500/20 text-[10px]">AVG_SEV</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Average Threat Score</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-yellow-500">{stats.avg_asset_severity}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.2} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-500">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <Badge variant="outline" className="text-indigo-500 bg-indigo-500/5 border-indigo-500/20 text-[10px]">AUTO_SOAR</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Actions Deployed</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-indigo-400">4 Actions</h3>
          </div>
        </CyberCard>
      </div>

      {/* Main Database Table & Inspect columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Assets Database Table */}
        <Card className="lg:col-span-2 bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 flex flex-col sm:flex-row sm:items-center justify-between pb-4 gap-4">
            <div>
              <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
                <Search className="h-4 w-4 text-primary" />
                Endpoint Database Registry
              </CardTitle>
              <CardDescription>Click a host row below to inspect its unique users, running processes, and remediation cards</CardDescription>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="relative w-48">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                <Input 
                  placeholder="Filter by Host / IP..." 
                  className="pl-8 h-8 text-[11px] bg-background/50 border-border/40"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              <select
                value={criticalityFilter}
                onChange={(e) => setCriticalityFilter(e.target.value)}
                className="bg-background/80 border border-border/40 text-xs px-2.5 py-1 rounded-lg text-foreground focus:ring-1 focus:ring-primary outline-none h-8"
              >
                <option value="all">All Criticalities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </CardHeader>
          
          <CardContent className="p-0">
            <div className="overflow-x-auto max-h-[500px] overflow-y-auto custom-scrollbar">
              <Table>
                <TableHeader>
                  <TableRow className="border-border/30 bg-muted/20 hover:bg-transparent">
                    <TableHead className="pl-6 font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Host/IP</TableHead>
                    <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Criticality</TableHead>
                    <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Role</TableHead>
                    <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Business Unit</TableHead>
                    <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Alerts</TableHead>
                    <TableHead className="pr-6 text-right font-mono text-[9px] uppercase font-black text-muted-foreground/60 tracking-wider">Suppr.</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAssets.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-12 text-muted-foreground font-semibold">
                        No endpoints found in this database view.
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredAssets.map((asset, idx) => {
                      const isSelected = selectedAssetIdx === idx;
                      return (
                        <TableRow 
                          key={idx} 
                          onClick={() => setSelectedAssetIdx(isSelected ? null : idx)}
                          className={`hover:bg-muted/10 border-border/10 cursor-pointer transition-colors
                            ${isSelected ? "bg-primary/5 hover:bg-primary/5 font-bold" : ""}`}
                        >
                          <TableCell className="pl-6">
                            <div className="flex flex-col">
                              <span className="font-mono text-xs text-foreground font-bold">{asset.hostname}</span>
                              <span className="font-mono text-[10px] text-muted-foreground/60">{asset.ip}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge className={getCriticalityBadge(asset.criticality)}>
                              {asset.criticality}
                            </Badge>
                          </TableCell>
                          <TableCell className="font-mono text-xs font-semibold capitalize text-foreground/80">
                            {asset.host_role?.replace("_", " ")}
                          </TableCell>
                          <TableCell className="font-mono text-xs text-muted-foreground">
                            {asset.business_unit}
                          </TableCell>
                          <TableCell className="font-mono text-xs font-bold text-rose-400">
                            {asset.total_alerts?.toLocaleString()}
                          </TableCell>
                          <TableCell className="pr-6 text-right font-mono text-xs text-emerald-400 font-bold">
                            {asset.suppression_rate}%
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Side Inspector Deck */}
        <div className="space-y-6">
          {selectedAssetIdx === null ? (
            <>
              {/* Criticality Breakdown Chart when no asset is selected */}
              <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
                <CardHeader className="border-b border-border/40 pb-4">
                  <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
                    <Activity className="h-4 w-4 text-warning" />
                    Criticality Breakdown
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="h-[200px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={criticalityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={9} tickLine={false} axisLine={false} />
                        <YAxis stroke="hsl(var(--muted-foreground))" fontSize={9} tickLine={false} axisLine={false} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "rgba(0, 0, 0, 0.85)",
                            backdropFilter: "blur(12px)",
                            border: "1px solid hsl(var(--border) / 0.4)",
                            borderRadius: "12px",
                            color: "white",
                          }}
                        />
                        <Bar dataKey="count" radius={[4, 4, 0, 0]} barSize={32}>
                          {criticalityData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Informative helper banner */}
              <Card className="bg-primary/5 border border-primary/20 p-6 rounded-xl flex items-start gap-3.5 shadow-lg">
                <Info className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="font-bold text-xs uppercase text-foreground tracking-wider font-grotesk">Inspection Deck</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Select any endpoint row from the database registry on the left to review logged processes, logged in active accounts, and execute SOAR remote patches.
                  </p>
                </div>
              </Card>
            </>
          ) : (
            <>
              {/* Asset Detail Inspection Card */}
              <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md animate-in fade-in-40 duration-200">
                <CardHeader className="border-b border-border/40 pb-4">
                  <Badge className="bg-primary/10 text-primary border-primary/20 w-fit mb-2 text-[10px] uppercase font-mono tracking-widest">
                    Live Telemetry inspect
                  </Badge>
                  <CardTitle className="text-lg font-bold font-mono text-foreground leading-none">
                    {data.asset_inventory[selectedAssetIdx].hostname}
                  </CardTitle>
                  <CardDescription className="font-mono text-[10px] text-muted-foreground/60 leading-none mt-1">
                    IP: {data.asset_inventory[selectedAssetIdx].ip}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6 space-y-4">
                  
                  {/* running processes */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-1.5 text-[9px] font-black uppercase tracking-wider text-muted-foreground/80 font-mono">
                      <Cpu size={12} className="text-primary" /> Logged Processes
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {data.asset_inventory[selectedAssetIdx].unique_processes?.map((proc, idx) => (
                        <Badge key={idx} variant="outline" className="text-[9px] font-mono bg-background/50 border-border/30 text-muted-foreground/90">
                          {proc}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* logged in users */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-1.5 text-[9px] font-black uppercase tracking-wider text-muted-foreground/80 font-mono">
                      <Users size={12} className="text-primary" /> Active Sessions
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {data.asset_inventory[selectedAssetIdx].unique_users?.map((usr, idx) => (
                        <Badge key={idx} variant="outline" className="text-[9px] font-mono bg-primary/5 border-primary/25 text-primary">
                          {usr}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* remote control actions */}
                  <div className="space-y-3 pt-4 border-t border-border/20">
                    <div className="text-[9px] font-black uppercase tracking-wider text-muted-foreground/60 font-mono">
                      Endpoint Remediation Deck
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <Button
                        size="sm"
                        onClick={() => handleAction(data.asset_inventory[selectedAssetIdx].ip, "Isolate Host")}
                        className="bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[9px] font-bold uppercase tracking-wider h-8"
                      >
                        Isolate Host
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => handleAction(data.asset_inventory[selectedAssetIdx].ip, "Patch Endpoint")}
                        className="bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[9px] font-bold uppercase tracking-wider h-8"
                      >
                        Patch Host
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => handleAction(data.asset_inventory[selectedAssetIdx].ip, "Revoke Session")}
                        className="bg-primary/10 hover:bg-primary/20 text-primary border border-primary/30 text-[9px] font-bold uppercase tracking-wider h-8"
                      >
                        Revoke Sessions
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => handleAction(data.asset_inventory[selectedAssetIdx].ip, "Restart Service")}
                        className="bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 text-[9px] font-bold uppercase tracking-wider h-8"
                      >
                        Restart Services
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
