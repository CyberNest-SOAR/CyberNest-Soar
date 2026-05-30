import { useDashboardData } from "@/hooks/useDashboardData";
import { PageHeader } from "@/components/PageHeader";
import { CyberCard } from "@/components/CyberCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Cpu, 
  RefreshCw, 
  ShieldCheck, 
  Brain, 
  Database,
  SlidersHorizontal,
  Workflow
} from "lucide-react";
import { 
  ResponsiveContainer, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  Radar,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell
} from "recharts";

interface ModelHealth {
  f1_score: number;
  precision: number;
  recall: number;
  total_classified: number;
  avg_confidence: number;
  min_confidence: number;
  max_confidence: number;
}

interface DecisionQueue {
  auto_closed_alerts: number;
  suppressed_alerts: number;
  escalated_alerts: number;
  low_confidence_detections: number;
}

interface AnalystFeedback {
  false_positives: number;
  true_positives: number;
  false_negatives: number;
  analyst_verdicts: Record<string, number>;
}

interface AiOperationsData {
  page: string;
  model_health: ModelHealth;
  ai_decision_queue: DecisionQueue;
  analyst_feedback: AnalystFeedback;
}

const fallbackDefault: AiOperationsData = {
  page: "AI Operations Center",
  model_health: {
    f1_score: 0,
    precision: 0,
    recall: 0,
    total_classified: 0,
    avg_confidence: 0,
    min_confidence: 0,
    max_confidence: 0
  },
  ai_decision_queue: {
    auto_closed_alerts: 0,
    suppressed_alerts: 0,
    escalated_alerts: 0,
    low_confidence_detections: 0
  },
  analyst_feedback: {
    false_positives: 0,
    true_positives: 0,
    false_negatives: 0,
    analyst_verdicts: {
      false_positive: 0,
      true_positive: 0,
      unknown: 0,
      benign: 0,
      suspicious: 0,
      investigating: 0
    }
  }
};

export default function AiOperationsPage() {
  const { data, loading, refetch } = useDashboardData<AiOperationsData>("ai-operations.json", fallbackDefault);

  // Safe object resolving using nullish coalescing
  const health = data?.model_health ?? fallbackDefault.model_health;
  const decisions = data?.ai_decision_queue ?? fallbackDefault.ai_decision_queue;
  const feedback = data?.analyst_feedback ?? fallbackDefault.analyst_feedback;

  // Format Recharts verdicts radar chart safely
  const radarChartData = Object.entries(feedback?.analyst_verdicts ?? fallbackDefault.analyst_feedback.analyst_verdicts).map(([key, val]) => ({
    subject: key.replace("_", " ").toUpperCase(),
    count: val,
    fullMark: Math.max(...Object.values(feedback?.analyst_verdicts ?? fallbackDefault.analyst_feedback.analyst_verdicts), 1)
  }));

  // Format Recharts dynamic decision outcomes bar chart safely
  const decisionChartData = [
    { name: "AUTO CLOSED", count: decisions?.auto_closed_alerts ?? 0, fill: "#10b981" },
    { name: "SUPPRESSED", count: decisions?.suppressed_alerts ?? 0, fill: "#eab308" },
    { name: "ESCALATED", count: decisions?.escalated_alerts ?? 0, fill: "#ef4444" },
    { name: "LOW CONFID.", count: decisions?.low_confidence_detections ?? 0, fill: "#3b82f6" }
  ];

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
          title={data?.page ?? fallbackDefault.page}
          description="Cognitive LLM agent decision metrics, model classifications, auto-containments, and analyst feedbacks"
          breadcrumbs={[{ label: "AI" }, { label: "AI Operations" }]}
        />
        <Button variant="outline" size="sm" onClick={refetch} className="font-mono text-xs border-border/40 flex items-center gap-2 hover:bg-primary/5">
          <RefreshCw className="h-3.5 w-3.5" /> Re-sync AI Engine
        </Button>
      </div>

      {/* Model Performance KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <CyberCard delay={0.05} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <Brain className="h-5 w-5" />
            </div>
            <Badge className="bg-primary/10 text-primary border border-primary/20 text-[10px]">COGNITIVE</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Total Classified Events</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-foreground">{(health?.total_classified ?? 0).toLocaleString()}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.1} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500">
              <ShieldCheck className="h-5 w-5 animate-pulse" />
            </div>
            <Badge variant="outline" className="text-emerald-500 bg-emerald-500/5 border-emerald-500/20 text-[10px]">MODEL_F1</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Model F1 Accuracy Rating</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-emerald-500">{(health?.f1_score ?? 0).toFixed(3)}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.15} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <SlidersHorizontal className="h-5 w-5 animate-pulse" />
            </div>
            <Badge variant="outline" className="text-purple-400 bg-purple-500/5 border-purple-500/20 text-[10px]">CONFIDENCE</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Average Model Confidence</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-purple-400">{(health?.avg_confidence ?? 0)}%</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.2} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-500">
              <Cpu className="h-5 w-5" />
            </div>
            <Badge variant="outline" className="text-indigo-400 bg-indigo-500/5 border-indigo-500/20 text-[10px]">AGENT_MAX</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Max Model Confidence</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-indigo-400">{(health?.max_confidence ?? 0)}%</h3>
          </div>
        </CyberCard>
      </div>

      {/* Model Health progress Bars & Recharts Radar campaigns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Model health progress metrics */}
        <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <Brain className="h-4 w-4 text-primary" />
              Evaluation Statistics
            </CardTitle>
            <CardDescription>Advanced model diagnostic stats</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-5 flex-1 flex flex-col justify-center">
            
            {/* Precision */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-[10px] uppercase font-bold tracking-widest text-muted-foreground">
                <span>Precision Rate</span>
                <span className="text-primary font-mono">{(health?.precision ?? 0) * 100}%</span>
              </div>
              <div className="h-1.5 w-full bg-muted/40 rounded-full overflow-hidden">
                <div className="h-full bg-primary" style={{ width: `${(health?.precision ?? 0) * 100}%` }} />
              </div>
            </div>

            {/* Recall */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-[10px] uppercase font-bold tracking-widest text-muted-foreground">
                <span>Recall Deflection Yield</span>
                <span className="text-emerald-500 font-mono">{(health?.recall ?? 0) * 100}%</span>
              </div>
              <div className="h-1.5 w-full bg-muted/40 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500" style={{ width: `${(health?.recall ?? 0) * 100}%` }} />
              </div>
            </div>

            {/* F1 */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-[10px] uppercase font-bold tracking-widest text-muted-foreground">
                <span>F1 Diagnostic Score</span>
                <span className="text-indigo-400 font-mono">{((health?.f1_score ?? 0) * 100).toFixed(1)}%</span>
              </div>
              <div className="h-1.5 w-full bg-muted/40 rounded-full overflow-hidden">
                <div className="h-full bg-indigo-400" style={{ width: `${(health?.f1_score ?? 0) * 100}%` }} />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* AI Decisions Bar Chart */}
        <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <SlidersHorizontal className="h-4 w-4 text-warning" />
              AI Automated Actions
            </CardTitle>
            <CardDescription>Inbound telemetry closed or escalated by LLM</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 flex-1 flex items-center justify-center">
            <div className="h-[210px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={decisionChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} barSize={24}>
                    {decisionChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Analyst Verdicts Radar Chart */}
        <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <Database className="h-4 w-4 text-primary" />
              Human Analyst Audits
            </CardTitle>
            <CardDescription>Analyst verdicts given on AI-assisted classifications</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 flex justify-center items-center">
            <div className="h-[220px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarChartData}>
                  <PolarGrid stroke="hsl(var(--border))" opacity={0.2} />
                  <PolarAngleAxis dataKey="subject" stroke="hsl(var(--muted-foreground))" fontSize={8} />
                  <PolarRadiusAxis angle={30} domain={[0, 'auto']} stroke="hsl(var(--muted-foreground))" fontSize={8} />
                  <Radar name="Verdicts" dataKey="count" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.25} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
