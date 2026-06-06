import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PageHeader } from "@/components/PageHeader";
import { CyberCard } from "@/components/CyberCard";
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Brain, ShieldCheck, Filter, BookOpen, Wrench, Mail, MessageSquare,
  RefreshCw, X, Activity, Zap, TrendingUp, AlertTriangle,
  ChevronRight, Circle, Cpu, DollarSign, Clock, Target, Star, BarChart2,
  Layers, Fingerprint, ThumbsUp, ThumbsDown, Eye,
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Cell, PieChart, Pie,
  LineChart, Line, CartesianGrid, Tooltip, Legend,
} from "recharts";
import { useDashboardData } from "@/hooks/useDashboardData";

const TOOLTIP_STYLE = {
  backgroundColor: "rgba(11,18,32,0.95)",
  backdropFilter: "blur(12px)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: "12px",
  color: "#f8fafc",
  fontSize: "11px",
};

const COLORS = {
  emerald: "#10b981",
  sky: "#22d3ee",
  violet: "#8b5cf6",
  amber: "#f59e0b",
  rose: "#f43f5e",
  indigo: "#6366f1",
  cyan: "#06b6d4",
  purple: "#a855f7",
};

const MODEL_ICONS: Record<string, React.ReactNode> = {
  "risk-scoring-ai": <ShieldCheck className="h-4 w-4" />,
  "noise-reduction-ai": <Filter className="h-4 w-4" />,
  "playbook-recommendation-ai": <BookOpen className="h-4 w-4" />,
  "patch-recommendation-ai": <Wrench className="h-4 w-4" />,
  "phishing-detection-ai": <Mail className="h-4 w-4" />,
  "llm-investigation-assistant": <MessageSquare className="h-4 w-4" />,
};

const MODEL_COLORS: Record<string, string> = {
  "risk-scoring-ai": COLORS.emerald,
  "noise-reduction-ai": COLORS.sky,
  "playbook-recommendation-ai": COLORS.violet,
  "patch-recommendation-ai": COLORS.amber,
  "phishing-detection-ai": COLORS.rose,
  "llm-investigation-assistant": COLORS.indigo,
};

function HealthDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    online: "bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]",
    warning: "bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.5)]",
    degraded: "bg-rose-400 shadow-[0_0_8px_rgba(244,63,94,0.5)]",
    offline: "bg-slate-500",
  };
  return <span className={`inline-block h-2 w-2 rounded-full ${colors[status] ?? "bg-slate-500"}`} />;
}

function MetricBar({ label, value, max = 1, color = "bg-primary" }: { label: string; value: number; max?: number; color?: string }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-center">
        <span className="text-[9px] uppercase tracking-widest font-bold text-muted-foreground/50">{label}</span>
        <span className="text-[10px] font-mono font-bold text-foreground">
          {max === 1 ? `${(value * 100).toFixed(1)}%` : value.toLocaleString()}
        </span>
      </div>
      <div className="h-1.5 w-full bg-muted/30 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className={`h-full rounded-full ${color}`}
        />
      </div>
    </div>
  );
}

function Gauge({ value, label, color }: { value: number; label: string; color: string }) {
  const r = 36;
  const circumference = 2 * Math.PI * r;
  const offset = circumference * (1 - value);
  return (
    <div className="flex flex-col items-center">
      <svg width="96" height="64" viewBox="0 0 96 64" className="overflow-visible">
        <path d="M 8 56 A 40 40 0 1 1 88 56" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6" strokeLinecap="round" />
        <path d="M 8 56 A 40 40 0 1 1 88 56" fill="none" stroke={color} strokeWidth="6" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset} transform="rotate(180, 48, 56)" />
      </svg>
      <span className="text-lg font-black font-mono -mt-2" style={{ color }}>{(value * 100).toFixed(1)}%</span>
      <span className="text-[8px] uppercase tracking-widest text-muted-foreground/50 mt-0.5">{label}</span>
    </div>
  );
}

const FALLBACK = { models: [], detection_explainability: [], analyst_feedback: {}, noise_reduction: {}, playbook_ai: {}, llm_telemetry: {} };

export default function AiOperationsPage() {
  const { data, loading, refetch } = useDashboardData<any>("ai-operations.json", FALLBACK);

  const models = data?.models ?? [];
  const explainability = data?.detection_explainability ?? [];
  const feedback = data?.analyst_feedback ?? {};
  const noise = data?.noise_reduction ?? {};
  const playbook = data?.playbook_ai ?? {};
  const llm = data?.llm_telemetry ?? {};

  const [selectedModel, setSelectedModel] = useState<any>(null);

  const feedbackChartData = useMemo(() => {
    return (feedback.feedback_trend ?? []).map((d: any) => ({
      ...d,
      total: d.tp + d.fp + d.suspicious,
    }));
  }, [feedback]);

  const noiseChartData = useMemo(() => {
    return (noise.daily_volume ?? []).map((d: any) => ({
      ...d,
      passed: d.received - d.suppressed,
    }));
  }, [noise]);

  const llmChartData = useMemo(() => {
    return (llm.daily_usage ?? []).map((d: any) => d);
  }, [llm]);

  const systemStatusColor = (models.some((m: any) => m.health_status === "warning" || m.health_status === "degraded")
    ? "text-amber-400 bg-amber-500/10 border-amber-500/25"
    : "text-emerald-400 bg-emerald-500/10 border-emerald-500/25");

  if (loading) {
    return (
      <div className="w-full h-full space-y-8 pb-20 animate-pulse">
        <div className="h-12 w-64 bg-muted/40 rounded-lg" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="h-28 rounded-2xl bg-muted/10 border border-border/20" />)}
        </div>
        <div className="h-[400px] rounded-2xl bg-muted/10 border border-border/20" />
      </div>
    );
  }

  const totalFeedback = (feedback.total_reviewed ?? 1);
  const fpRate = feedback.false_positives ? ((feedback.false_positives / totalFeedback) * 100).toFixed(1) : "0";
  const tpRate = feedback.true_positives ? ((feedback.true_positives / totalFeedback) * 100).toFixed(1) : "0";

  return (
    <div className="w-full h-full space-y-8 pb-20">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <PageHeader
          title="AI Operations Center"
          description="Internal intelligence: model health, detection explainability, and analyst feedback"
          breadcrumbs={[{ label: "AI" }, { label: "AI Operations" }]}
        />
        <div className="flex items-center gap-3 shrink-0">
          <Badge className={`border text-[10px] px-3 py-1 font-mono font-bold uppercase ${systemStatusColor}`}>
            <Circle className="h-2 w-2 mr-1.5 fill-current" />
            {models.some((m: any) => m.health_status === "warning") ? "WARNING" : "HEALTHY"}
          </Badge>
          <Button variant="outline" size="sm" onClick={refetch}
            className="font-mono text-xs border-border/40 gap-2 hover:bg-primary/5">
            <RefreshCw className="h-3.5 w-3.5" /> Sync
          </Button>
        </div>
      </div>

      {/* Top KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Executions", value: (data?.total_executions ?? 0).toLocaleString(), icon: <Cpu />, color: COLORS.violet },
          { label: "Avg Drift Score", value: `${((data?.average_drift ?? 0) * 100).toFixed(2)}%`, icon: <TrendingUp />, color: COLORS.amber },
          { label: "Active Models", value: `${models.filter((m: any) => m.health_status === "online").length} / ${models.length}`, icon: <Brain />, color: COLORS.emerald },
          { label: "LLM Cost (est.)", value: `$${(llm.estimated_cost ?? 0).toFixed(2)}`, icon: <DollarSign />, color: COLORS.indigo },
        ].map((kpi, i) => (
          <CyberCard key={kpi.label} delay={i * 0.06} className="bg-card/20 border-border/40">
            <div className="flex justify-between items-start mb-3">
              <div className="p-2.5 rounded-xl bg-opacity-10 border" style={{ backgroundColor: `${kpi.color}15`, borderColor: `${kpi.color}30`, color: kpi.color }}>
                {kpi.icon}
              </div>
            </div>
            <p className="text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground/50 mb-1">{kpi.label}</p>
            <p className="text-xl font-black font-mono" style={{ color: kpi.color }}>{kpi.value}</p>
          </CyberCard>
        ))}
      </div>

      {/* Section 1: AI Model Health */}
      <Card className="glass border-border/40 shadow-xl backdrop-blur-md overflow-hidden">
        <CardHeader className="border-b border-border/40 pb-4">
          <CardTitle className="text-lg font-bold flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            AI Model Health
          </CardTitle>
          <CardDescription>Per-model metrics including accuracy, precision, recall, F1, ROC-AUC, and drift</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/20 bg-muted/10">
                  <th className="text-left pl-6 py-3 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Model</th>
                  <th className="text-left py-3 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Version</th>
                  <th className="text-center py-3 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Status</th>
                  <th className="text-center py-3 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Accuracy</th>
                  <th className="text-center py-3 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Precision</th>
                  <th className="text-center py-3 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Recall</th>
                  <th className="text-center py-3 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">F1</th>
                  <th className="text-center py-3 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">ROC-AUC</th>
                  <th className="text-center py-3 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Drift</th>
                  <th className="text-right pr-6 py-3 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Requests</th>
                </tr>
              </thead>
              <tbody>
                {models.map((model: any, idx: number) => {
                  const color = MODEL_COLORS[model.id] ?? COLORS.violet;
                  const driftPct = (model.drift_score * 100).toFixed(1);
                  return (
                    <motion.tr
                      key={model.id}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.04 }}
                      onClick={() => setSelectedModel(model)}
                      className="border-b border-border/10 hover:bg-muted/10 transition-colors cursor-pointer group"
                    >
                      <td className="pl-6 py-3">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg" style={{ backgroundColor: `${color}15`, color }}>
                            {MODEL_ICONS[model.id] ?? <Cpu className="h-4 w-4" />}
                          </div>
                          <span className="font-bold text-xs">{model.model_name}</span>
                        </div>
                      </td>
                      <td className="py-3 font-mono text-[10px] text-muted-foreground/70">{model.model_version}</td>
                      <td className="py-3 text-center"><HealthDot status={model.health_status} /></td>
                      <td className="py-3 text-center font-mono text-xs font-bold" style={{ color: model.accuracy >= 0.9 ? COLORS.emerald : model.accuracy >= 0.8 ? COLORS.amber : COLORS.rose }}>
                        {(model.accuracy * 100).toFixed(1)}%
                      </td>
                      <td className="py-3 text-center font-mono text-xs text-muted-foreground/80">{(model.precision * 100).toFixed(1)}%</td>
                      <td className="py-3 text-center font-mono text-xs text-muted-foreground/80">{(model.recall * 100).toFixed(1)}%</td>
                      <td className="py-3 text-center font-mono text-xs text-muted-foreground/80">{(model.f1_score * 100).toFixed(1)}%</td>
                      <td className="py-3 text-center font-mono text-xs text-muted-foreground/80">{(model.roc_auc * 100).toFixed(1)}%</td>
                      <td className="py-3 text-center">
                        <span className={`font-mono text-[10px] font-bold ${driftPct > "15" ? "text-rose-400" : driftPct > "8" ? "text-amber-400" : "text-emerald-400"}`}>
                          {driftPct}%
                        </span>
                      </td>
                      <td className="pr-6 py-3 text-right font-mono text-xs text-muted-foreground/70">{model.request_count.toLocaleString()}</td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Section 2: Detection Explainability */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Fingerprint className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-bold">Detection Explainability</h2>
          <p className="text-xs text-muted-foreground/60 ml-auto">Understanding why the AI made each decision</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {explainability.map((item: any, idx: number) => (
            <motion.div
              key={item.alert_id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.08 }}
              className="rounded-2xl border border-border/30 bg-card/20 backdrop-blur-md p-5 hover:bg-card/30 transition-all"
            >
              <div className="flex items-center justify-between mb-3">
                <Badge variant="outline" className="font-mono text-[9px]">{item.alert_id}</Badge>
                <Badge className="bg-primary/10 text-primary border-primary/20 text-[10px]">v{item.model_version}</Badge>
              </div>
              <div className="flex items-baseline gap-3 mb-4">
                <div>
                  <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50">Risk Score</p>
                  <span className="text-3xl font-black font-mono" style={{ color: item.risk_score >= 90 ? COLORS.rose : item.risk_score >= 70 ? COLORS.amber : COLORS.emerald }}>
                    {item.risk_score}
                  </span>
                </div>
                <div>
                  <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50">Confidence</p>
                  <span className="text-xl font-black font-mono text-primary">{(item.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
              <div className="space-y-1.5 mb-4">
                <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50">Top Contributors</p>
                {item.top_features?.slice(0, 4).map((f: any) => (
                  <div key={f.name} className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 bg-muted/30 rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${f.contribution * 100}%`, backgroundColor: COLORS.violet }} />
                    </div>
                    <span className="text-[9px] font-mono text-muted-foreground/60 w-24 text-right">{f.name}</span>
                    <span className="text-[9px] font-mono font-bold text-muted-foreground/80 w-8 text-right">{(f.contribution * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
              <div className="bg-muted/10 rounded-xl p-3 border border-border/20">
                <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50 mb-1">Reason</p>
                <p className="text-[11px] text-foreground/70 leading-relaxed">{item.decision_reason}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Section 3: Analyst Feedback + Section 4: Noise Reduction */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Analyst Feedback */}
        <Card className="glass border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold flex items-center gap-2">
              <ThumbsUp className="h-5 w-5 text-emerald-400" />
              Analyst Feedback
            </CardTitle>
            <CardDescription>Human verification results used for model retraining</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-5">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                { label: "True Positives", value: feedback.true_positives ?? 0, color: COLORS.emerald, icon: <ShieldCheck className="h-3 w-3" /> },
                { label: "False Positives", value: feedback.false_positives ?? 0, color: COLORS.rose, icon: <AlertTriangle className="h-3 w-3" /> },
                { label: "Suspicious", value: feedback.suspicious ?? 0, color: COLORS.amber, icon: <Eye className="h-3 w-3" /> },
                { label: "Escalated", value: feedback.escalated ?? 0, color: COLORS.violet, icon: <Target className="h-3 w-3" /> },
                { label: "Closed", value: feedback.closed ?? 0, color: COLORS.sky, icon: <ThumbsDown className="h-3 w-3" /> },
              ].map(s => (
                <div key={s.label} className="bg-muted/10 rounded-xl p-3 border border-border/20">
                  <div className="flex items-center gap-1.5 text-muted-foreground/50 mb-1">
                    {s.icon}
                    <span className="text-[9px] uppercase tracking-widest font-bold">{s.label}</span>
                  </div>
                  <p className="text-xl font-black font-mono" style={{ color: s.color }}>{s.value.toLocaleString()}</p>
                </div>
              ))}
            </div>
            <div className="flex gap-3">
              <div className="flex-1 bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-3">
                <p className="text-[9px] uppercase tracking-widest text-emerald-400/60">TP Rate</p>
                <p className="text-2xl font-black font-mono text-emerald-400">{tpRate}%</p>
              </div>
              <div className="flex-1 bg-rose-500/5 border border-rose-500/20 rounded-xl p-3">
                <p className="text-[9px] uppercase tracking-widest text-rose-400/60">FP Rate</p>
                <p className="text-2xl font-black font-mono text-rose-400">{fpRate}%</p>
              </div>
            </div>
            {feedbackChartData.length > 0 && (
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={feedbackChartData} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                    <XAxis dataKey="date" tick={{ fontSize: 8, fill: "#64748b" }} tickFormatter={(v: string) => v.slice(5)} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 8, fill: "#64748b" }} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                    <Bar dataKey="tp" name="TP" stackId="a" fill={COLORS.emerald} radius={[0, 0, 0, 0]} />
                    <Bar dataKey="fp" name="FP" stackId="a" fill={COLORS.rose} radius={[0, 0, 0, 0]} />
                    <Bar dataKey="suspicious" name="Suspicious" stackId="a" fill={COLORS.amber} radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Noise Reduction AI */}
        <Card className="glass border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold flex items-center gap-2">
              <Layers className="h-5 w-5 text-sky-400" />
              Noise Reduction AI
            </CardTitle>
            <CardDescription>Alert deduplication and suppression efficiency</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-5">
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Total Alerts", value: (noise.total_alerts ?? 0).toLocaleString(), color: COLORS.sky },
                { label: "Suppressed", value: (noise.alerts_suppressed ?? 0).toLocaleString(), color: COLORS.cyan },
                { label: "Duplicates", value: (noise.duplicate_alerts ?? 0).toLocaleString(), color: COLORS.violet },
                { label: "Analyst Reviewed", value: (noise.analyst_reviewed ?? 0).toLocaleString(), color: COLORS.emerald },
              ].map(s => (
                <div key={s.label} className="bg-muted/10 rounded-xl p-3 border border-border/20">
                  <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50 mb-1">{s.label}</p>
                  <p className="text-lg font-black font-mono" style={{ color: s.color }}>{s.value}</p>
                </div>
              ))}
            </div>
            <div className="bg-sky-500/5 border border-sky-500/20 rounded-xl p-4 text-center">
              <p className="text-[10px] uppercase tracking-widest text-sky-400/60 mb-1">ALERT REDUCTION RATE</p>
              <p className="text-4xl font-black font-mono text-sky-400">{(noise.reduction_percentage ?? 0).toFixed(1)}%</p>
              <p className="text-xs text-muted-foreground/40 mt-1">Noise eliminated before analyst review</p>
            </div>
            {noiseChartData.length > 0 && (
              <div className="h-36">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={noiseChartData} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                    <XAxis dataKey="date" tick={{ fontSize: 8, fill: "#64748b" }} tickFormatter={(v: string) => v.slice(5)} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 8, fill: "#64748b" }} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                    <Bar dataKey="suppressed" name="Suppressed" stackId="a" fill={COLORS.sky} radius={[0, 0, 0, 0]} />
                    <Bar dataKey="clustered" name="Clustered" stackId="a" fill={COLORS.cyan} radius={[0, 0, 0, 0]} />
                    <Bar dataKey="passed" name="To Review" stackId="a" fill={COLORS.emerald} radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Section 5: Playbook AI + Section 6: LLM Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Playbook AI */}
        <Card className="glass border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-violet-400" />
              Playbook AI
            </CardTitle>
            <CardDescription>Automated playbook recommendations and execution metrics</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-5">
            <div className="grid grid-cols-1 gap-3">
              <div className="bg-violet-500/5 border border-violet-500/20 rounded-xl p-4 flex items-center justify-between">
                <div>
                  <p className="text-[9px] uppercase tracking-widest text-violet-400/60 mb-1">Recommended</p>
                  <p className="text-lg font-black font-mono text-violet-400">{playbook.recommended_playbook ?? "—"}</p>
                </div>
                <div className="text-right">
                  <p className="text-[9px] uppercase tracking-widest text-violet-400/60 mb-1">Confidence</p>
                  <p className="text-2xl font-black font-mono text-amber-400">{((playbook.confidence ?? 0) * 100).toFixed(0)}%</p>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Success Rate", value: `${((playbook.success_rate ?? 0) * 100).toFixed(1)}%`, color: COLORS.emerald },
                { label: "Avg Response", value: `${playbook.average_response_time ?? "—"}s`, color: COLORS.sky },
                { label: "Override Rate", value: `${((playbook.analyst_override_rate ?? 0) * 100).toFixed(1)}%`, color: COLORS.amber },
                { label: "Mode", value: playbook.execution_mode?.replace(/_/g, " ") ?? "—", color: COLORS.violet },
              ].map(s => (
                <div key={s.label} className="bg-muted/10 rounded-xl p-3 border border-border/20">
                  <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50 mb-1">{s.label}</p>
                  <p className="text-lg font-black font-mono" style={{ color: s.color }}>{s.value}</p>
                </div>
              ))}
            </div>
            <div>
              <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50 mb-3">RECENT RECOMMENDATIONS</p>
              <div className="space-y-2">
                {(playbook.recent_recommendations ?? []).map((r: any) => (
                  <div key={r.playbook} className="flex items-center justify-between bg-muted/10 rounded-lg px-3 py-2 border border-border/20">
                    <div className="flex items-center gap-2">
                      <span className="h-1.5 w-1.5 rounded-full bg-violet-400" />
                      <span className="text-xs font-mono font-bold text-foreground/80">{r.playbook}</span>
                    </div>
                    <div className="flex items-center gap-3 text-[10px] font-mono text-muted-foreground/60">
                      <span>{r.count.toLocaleString()}x</span>
                      <span className={r.success_rate >= 0.95 ? "text-emerald-400" : "text-amber-400"}>{(r.success_rate * 100).toFixed(0)}%</span>
                      <span>{r.avg_time}s</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* LLM Telemetry */}
        <Card className="glass border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-indigo-400" />
              LLM Telemetry
            </CardTitle>
            <CardDescription>Token usage, latency, cost, and analyst feedback for the investigation assistant</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-5">
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Total Requests", value: (llm.total_requests ?? 0).toLocaleString(), icon: <BarChart2 className="h-3 w-3" />, color: COLORS.indigo },
                { label: "Token Usage", value: (llm.token_usage ?? 0).toLocaleString(), icon: <Zap className="h-3 w-3" />, color: COLORS.cyan },
                { label: "Avg Latency", value: `${llm.average_latency ?? "—"}s`, icon: <Clock className="h-3 w-3" />, color: COLORS.sky },
                { label: "Est. Cost", value: `$${(llm.estimated_cost ?? 0).toFixed(2)}`, icon: <DollarSign className="h-3 w-3" />, color: COLORS.emerald },
                { label: "Failed Requests", value: (llm.failed_requests ?? 0).toLocaleString(), icon: <AlertTriangle className="h-3 w-3" />, color: COLORS.rose },
                { label: "Hallucination Reports", value: (llm.hallucination_reports ?? 0).toLocaleString(), icon: <AlertTriangle className="h-3 w-3" />, color: COLORS.amber },
              ].map(s => (
                <div key={s.label} className="bg-muted/10 rounded-xl p-3 border border-border/20">
                  <div className="flex items-center gap-1.5 text-muted-foreground/50 mb-1">
                    {s.icon}
                    <span className="text-[9px] uppercase tracking-widest font-bold">{s.label}</span>
                  </div>
                  <p className="text-lg font-black font-mono" style={{ color: s.color }}>{s.value}</p>
                </div>
              ))}
            </div>
            <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-3 flex items-center justify-between">
              <div>
                <p className="text-[9px] uppercase tracking-widest text-amber-400/60">Analyst Feedback Score</p>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex gap-0.5">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className={`h-4 w-4 ${i < Math.round(llm.analyst_feedback_score ?? 0) ? "fill-amber-400 text-amber-400" : "text-muted-foreground/20"}`} />
                    ))}
                  </div>
                  <span className="text-lg font-black font-mono text-amber-400">{(llm.analyst_feedback_score ?? 0).toFixed(2)}</span>
                </div>
              </div>
              <span className="text-3xl font-black font-mono text-amber-400/30">/ 5</span>
            </div>
            {llmChartData.length > 0 && (
              <div className="h-36">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={llmChartData} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis dataKey="date" tick={{ fontSize: 8, fill: "#64748b" }} tickFormatter={(v: string) => v.slice(5)} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 8, fill: "#64748b" }} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                    <Line type="monotone" dataKey="requests" name="Requests" stroke={COLORS.indigo} strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="failed" name="Failed" stroke={COLORS.rose} strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Model Detail Drawer */}
      <AnimatePresence>
        {selectedModel && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedModel(null)}
              className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
            />
            <ModelDrawer model={selectedModel} onClose={() => setSelectedModel(null)} />
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

function ModelDrawer({ model, onClose }: { model: any; onClose: () => void }) {
  const color = MODEL_COLORS[model.id] ?? COLORS.violet;
  const icon = MODEL_ICONS[model.id] ?? <Cpu className="h-5 w-5" />;
  const driftPct = (model.drift_score * 100).toFixed(1);

  const metrics = [
    { label: "Accuracy", value: model.accuracy, color: COLORS.emerald, gauge: true },
    { label: "Precision", value: model.precision, color: COLORS.sky, gauge: true },
    { label: "Recall", value: model.recall, color: COLORS.violet, gauge: true },
    { label: "F1 Score", value: model.f1_score, color: COLORS.amber, gauge: true },
    { label: "ROC-AUC", value: model.roc_auc, color: COLORS.cyan, gauge: true },
  ];

  const gaugeColors = [COLORS.emerald, COLORS.sky, COLORS.violet, COLORS.amber, COLORS.cyan];

  return (
    <motion.div
      initial={{ x: "100%", opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: "100%", opacity: 0 }}
      transition={{ type: "spring", damping: 28, stiffness: 280 }}
      className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-[hsl(var(--background))] border-l border-border/50 shadow-2xl flex flex-col"
    >
      <div className="flex items-center gap-3 px-6 py-5 border-b border-border/30" style={{ backgroundColor: `${color}08` }}>
        <div className="p-2.5 rounded-xl border" style={{ backgroundColor: `${color}15`, borderColor: `${color}30`, color }}>
          {icon}
        </div>
        <div className="flex-1">
          <p className="text-[9px] font-mono uppercase tracking-widest text-muted-foreground/50">{model.id?.replace(/-/g, " ").toUpperCase()}</p>
          <h2 className="text-base font-bold">{model.model_name}</h2>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8 rounded-lg hover:bg-muted/30">
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex items-center gap-3 px-6 py-3 border-b border-border/20 bg-muted/5">
        <HealthDot status={model.health_status} />
        <span className="text-xs capitalize font-mono text-muted-foreground">{model.health_status}</span>
        <Separator orientation="vertical" className="h-4" />
        <span className="text-xs font-mono text-muted-foreground">v{model.model_version}</span>
        <Separator orientation="vertical" className="h-4" />
        <span className="text-xs font-mono font-bold" style={{ color }}>{(model.accuracy * 100).toFixed(1)}%</span>
      </div>

      <ScrollArea className="flex-1 px-6 py-5">
        <div className="space-y-6">
          {/* Gauge metrics */}
          <div>
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground/50 mb-4">PERFORMANCE METRICS</p>
            <div className="grid grid-cols-3 gap-3">
              {metrics.map((m, i) => (
                <div key={m.label} className="flex flex-col items-center bg-muted/10 rounded-xl p-3 border border-border/20">
                  <div className="relative w-full flex justify-center">
                    <svg width="72" height="48" viewBox="0 0 72 48" className="overflow-visible">
                      <path d="M 6 42 A 30 30 0 1 1 66 42" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="5" strokeLinecap="round" />
                      <path d="M 6 42 A 30 30 0 1 1 66 42" fill="none" stroke={gaugeColors[i]} strokeWidth="5" strokeLinecap="round"
                        strokeDasharray={2 * Math.PI * 30} strokeDashoffset={2 * Math.PI * 30 * (1 - m.value)}
                        transform="rotate(180, 36, 42)" />
                    </svg>
                  </div>
                  <span className="text-base font-black font-mono" style={{ color: gaugeColors[i] }}>{(m.value * 100).toFixed(1)}%</span>
                  <span className="text-[8px] uppercase tracking-widest text-muted-foreground/50">{m.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Model info */}
          <div>
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground/50 mb-3">MODEL INFO</p>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Version", value: model.model_version },
                { label: "Dataset", value: model.dataset_version },
                { label: "Last Training", value: new Date(model.last_training).toLocaleDateString() },
                { label: "Requests", value: model.request_count.toLocaleString() },
              ].map(s => (
                <div key={s.label} className="bg-muted/10 rounded-xl p-3 border border-border/20">
                  <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50 mb-1">{s.label}</p>
                  <p className="text-sm font-bold font-mono text-foreground/80">{s.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Drift indicator */}
          <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4">
            <p className="text-[10px] uppercase tracking-widest text-amber-400/60 mb-2">DRIFT SCORE</p>
            <div className="flex items-center gap-4">
              <span className={`text-3xl font-black font-mono ${driftPct > "15" ? "text-rose-400" : driftPct > "8" ? "text-amber-400" : "text-emerald-400"}`}>
                {driftPct}%
              </span>
              <div className="flex-1 h-2 bg-muted/30 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all" style={{
                  width: `${Math.min(parseFloat(driftPct) * 3, 100)}%`,
                  backgroundColor: parseFloat(driftPct) > 15 ? COLORS.rose : parseFloat(driftPct) > 8 ? COLORS.amber : COLORS.emerald,
                }} />
              </div>
            </div>
            <p className="text-[10px] text-muted-foreground/40 mt-2">
              {parseFloat(driftPct) > 15 ? "Retraining recommended — significant drift detected" :
               parseFloat(driftPct) > 8 ? "Moderate drift — monitor closely" :
               "Within acceptable range"}
            </p>
          </div>
        </div>
      </ScrollArea>
    </motion.div>
  );
}
