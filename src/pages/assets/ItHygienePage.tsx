import { useDashboardData } from "@/hooks/useDashboardData";
import { PageHeader } from "@/components/PageHeader";
import { CyberCard } from "@/components/CyberCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  ShieldAlert, 
  CheckCircle2, 
  RefreshCw, 
  SlidersHorizontal,
  Compass,
  AlertTriangle,
  Award
} from "lucide-react";
import { 
  ResponsiveContainer, 
  RadialBarChart, 
  RadialBar, 
  PolarAngleAxis,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell
} from "recharts";

interface HygieneScore {
  overall: number;
  breakdown: {
    patch_hygiene: number;
    authentication_hygiene: number;
    logging_hygiene: number;
    integrity_hygiene: number;
    threat_hygiene: number;
  };
}

interface RiskTrends {
  total_issues: number;
  patch_issues: number;
  auth_issues: number;
  config_issues: number;
  integrity_issues: number;
  threat_issues: number;
  vulnerable_hosts: number;
}

interface Compliance {
  nist_coverage: number;
  cis_coverage: number;
  mitre_coverage: number;
}

interface ItHygieneData {
  page: string;
  hygiene_score: HygieneScore;
  risk_trends: RiskTrends;
  compliance: Compliance;
}

const fallbackDefault: ItHygieneData = {
  page: "IT Hygiene & Exposure",
  hygiene_score: {
    overall: 0,
    breakdown: {
      patch_hygiene: 0,
      authentication_hygiene: 0,
      logging_hygiene: 0,
      integrity_hygiene: 0,
      threat_hygiene: 0
    }
  },
  risk_trends: {
    total_issues: 0,
    patch_issues: 0,
    auth_issues: 0,
    config_issues: 0,
    integrity_issues: 0,
    threat_issues: 0,
    vulnerable_hosts: 0
  },
  compliance: {
    nist_coverage: 0,
    cis_coverage: 0,
    mitre_coverage: 0
  }
};

export default function ItHygienePage() {
  const { data, loading, refetch } = useDashboardData<ItHygieneData>("it-hygiene.json", fallbackDefault);

  // Safe destructuring of objects using nullish coalescing
  const hygiene = data?.hygiene_score ?? fallbackDefault.hygiene_score;
  const breakdown = hygiene?.breakdown ?? fallbackDefault.hygiene_score.breakdown;
  const risks = data?.risk_trends ?? fallbackDefault.risk_trends;
  const compliance = data?.compliance ?? fallbackDefault.compliance;

  // Format Recharts dynamic radial chart safely
  const overallRadialData = [{
    name: "Overall",
    value: hygiene?.overall ?? 0,
    fill: "hsl(var(--critical))"
  }];

  // Format Recharts issue trends bar chart safely
  const riskTrendsData = [
    { name: "PATCHING", count: risks?.patch_issues ?? 0, fill: "hsl(var(--cyber-blue))" },
    { name: "CONFIG", count: risks?.config_issues ?? 0, fill: "hsl(var(--warning))" },
    { name: "INTEGRITY", count: risks?.integrity_issues ?? 0, fill: "hsl(var(--secondary))" },
    { name: "THREATS", count: risks?.threat_issues ?? 0, fill: "hsl(var(--critical))" }
  ];

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
          title={data?.page ?? fallbackDefault.page}
          description="System-wide credential strengths, host patching rates, compliance coverage, and critical risks"
          breadcrumbs={[{ label: "Assets" }, { label: "IT Hygiene" }]}
        />
        <Button variant="outline" size="sm" onClick={refetch} className="font-mono text-xs border-border/40 flex items-center gap-2 hover:bg-primary/5">
          <RefreshCw className="h-3.5 w-3.5" /> Scan Hygiene
        </Button>
      </div>

      {/* Main Breakdown Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Overall Score Radial Gauge */}
        <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <Compass className="h-4 w-4 text-rose-500 animate-spin" style={{ animationDuration: '8s' }} />
              Overall Hygiene Score
            </CardTitle>
            <CardDescription>Consolidated exposure health rating index</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 flex flex-col items-center justify-center flex-1">
            <div className="h-[180px] w-full relative flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart 
                  innerRadius="75%" 
                  outerRadius="100%" 
                  data={overallRadialData} 
                  startAngle={180} 
                  endAngle={0}
                >
                  <PolarAngleAxis
                    type="number"
                    domain={[0, 100]}
                    angleAxisId={0}
                    tick={false}
                  />
                  <RadialBar 
                    background 
                    dataKey="value" 
                    cornerRadius={8}
                  />
                </RadialBarChart>
              </ResponsiveContainer>
              <div className="absolute flex flex-col items-center justify-center mt-6">
                <span className="text-4xl font-black font-mono tracking-tighter text-rose-500">{hygiene?.overall ?? 0}%</span>
                <span className="text-[10px] font-black uppercase text-muted-foreground/60 tracking-wider">CRITICAL RISKS</span>
              </div>
            </div>
            <div className="p-4 rounded-xl bg-rose-500/5 border border-rose-500/20 text-center w-full mt-4 text-xs font-mono font-semibold text-rose-400">
              EXPOSURE ALERT: Action required on missing patch nodes.
            </div>
          </CardContent>
        </Card>

        {/* Sub-Hygiene Progress Cards */}
        <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              Category Metrics
            </CardTitle>
            <CardDescription>Hygiene strength analysis per subsystem layer</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-4 flex-1 flex flex-col justify-center">
            
            {/* Patching */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-[10px] uppercase font-bold tracking-widest text-muted-foreground">
                <span>Patch Compliance</span>
                <span className="text-primary font-mono">{(breakdown?.patch_hygiene ?? 0).toFixed(1)}%</span>
              </div>
              <div className="h-1.5 w-full bg-muted/40 rounded-full overflow-hidden">
                <div className="h-full bg-primary" style={{ width: `${breakdown?.patch_hygiene ?? 0}%` }} />
              </div>
            </div>

            {/* Auth */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-[10px] uppercase font-bold tracking-widest text-muted-foreground">
                <span>Authentication Strength</span>
                <span className="text-emerald-500 font-mono">{(breakdown?.authentication_hygiene ?? 0)}%</span>
              </div>
              <div className="h-1.5 w-full bg-muted/40 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500" style={{ width: `${breakdown?.authentication_hygiene ?? 0}%` }} />
              </div>
            </div>

            {/* Logging */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-[10px] uppercase font-bold tracking-widest text-muted-foreground">
                <span>Log Integrity Coverage</span>
                <span className="text-primary font-mono">{(breakdown?.logging_hygiene ?? 0).toFixed(1)}%</span>
              </div>
              <div className="h-1.5 w-full bg-muted/40 rounded-full overflow-hidden">
                <div className="h-full bg-primary" style={{ width: `${breakdown?.logging_hygiene ?? 0}%` }} />
              </div>
            </div>

            {/* Threat */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-[10px] uppercase font-bold tracking-widest text-muted-foreground">
                <span>Threat Exposure Defense</span>
                <span className="text-amber-500 font-mono">{(breakdown?.threat_hygiene ?? 0).toFixed(1)}%</span>
              </div>
              <div className="h-1.5 w-full bg-muted/40 rounded-full overflow-hidden">
                <div className="h-full bg-amber-500" style={{ width: `${breakdown?.threat_hygiene ?? 0}%` }} />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Risk Issues Breakdown Bar Chart */}
        <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-warning" />
              Outstanding Exposure Issues
            </CardTitle>
            <CardDescription>Open vulnerabilities mapped by threat category</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 flex-1 flex items-center justify-center">
            <div className="h-[230px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={riskTrendsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={9} tickLine={false} axisLine={false} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={9} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      backdropFilter: "blur(12px)",
                      border: "1px solid hsl(var(--border) / 0.4)",
                      borderRadius: "12px",
                      color: "white"
                    }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} barSize={24}>
                    {riskTrendsData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Compliance Coverage & Checklist */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* NIST */}
        <CyberCard className="bg-card/20 border-border/40">
          <div className="flex justify-between items-center mb-4">
            <div className="p-2 bg-primary/10 border border-primary/20 text-primary rounded-xl">
              <Award className="h-5 w-5" />
            </div>
            <Badge className="bg-primary/10 text-primary border border-primary/20 text-[9px] font-mono">NIST Framework</Badge>
          </div>
          <div className="space-y-2">
            <p className="text-[10px] font-black uppercase text-muted-foreground/60 tracking-wider">NIST Compliance coverage</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-foreground">{compliance?.nist_coverage ?? 0}%</h3>
            <div className="h-1 w-full bg-muted/40 rounded-full overflow-hidden">
              <div className="h-full bg-primary" style={{ width: `${compliance?.nist_coverage ?? 0}%` }} />
            </div>
          </div>
        </CyberCard>

        {/* CIS */}
        <CyberCard className="bg-card/20 border-border/40">
          <div className="flex justify-between items-center mb-4">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 rounded-xl">
              <Award className="h-5 w-5" />
            </div>
            <Badge className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[9px] font-mono">CIS Controls</Badge>
          </div>
          <div className="space-y-2">
            <p className="text-[10px] font-black uppercase text-muted-foreground/60 tracking-wider">CIS Audit alignment</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-foreground">{compliance?.cis_coverage ?? 0}%</h3>
            <div className="h-1 w-full bg-muted/40 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500" style={{ width: `${compliance?.cis_coverage ?? 0}%` }} />
            </div>
          </div>
        </CyberCard>

        {/* MITRE */}
        <CyberCard className="bg-card/20 border-border/40">
          <div className="flex justify-between items-center mb-4">
            <div className="p-2 bg-purple-500/10 border border-purple-500/20 text-purple-400 rounded-xl">
              <Award className="h-5 w-5" />
            </div>
            <Badge className="bg-purple-500/10 text-purple-400 border border-purple-500/20 text-[9px] font-mono">MITRE ATT&CK</Badge>
          </div>
          <div className="space-y-2">
            <p className="text-[10px] font-black uppercase text-muted-foreground/60 tracking-wider">Tactical Mitigation Coverage</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-foreground">{compliance?.mitre_coverage ?? 0}%</h3>
            <div className="h-1 w-full bg-muted/40 rounded-full overflow-hidden">
              <div className="h-full bg-purple-500" style={{ width: `${compliance?.mitre_coverage ?? 0}%` }} />
            </div>
          </div>
        </CyberCard>

      </div>
    </div>
  );
}
