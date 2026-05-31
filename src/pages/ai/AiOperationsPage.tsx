import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PageHeader } from "@/components/PageHeader";
import { CyberCard } from "@/components/CyberCard";
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Brain, ShieldCheck, Volume2, BookOpen, Wrench, Mail, MessageSquare,
  RefreshCw, X, Activity, Zap, TrendingUp, TrendingDown, AlertTriangle,
  ChevronRight, Circle, Cpu, DollarSign, Clock, Target, Star, BarChart2,
  Layers, Filter,
} from "lucide-react";
import {
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, Tooltip, BarChart, Bar, XAxis, YAxis, Cell, PieChart, Pie,
  LineChart, Line, CartesianGrid, Area, AreaChart, Legend,
} from "recharts";

// ─── Types ───────────────────────────────────────────────────────────────────

interface ModelOverview {
  model_name: string;
  id: string;
  health_status: "online" | "warning" | "degraded" | "offline";
  accuracy: number;
  last_execution: string;
  request_count: number;
  drift_score: number;
}

interface AiOverviewData {
  timestamp: string;
  system_status: string;
  total_executions: number;
  average_drift: number;
  models: ModelOverview[];
}

interface LiveEvent {
  timestamp: string;
  model_id: string;
  event_id?: string;
  confidence?: number;
  outcome: string;
  latency: number;
  token_cost?: number;
  drift_alert: boolean;
}

// ─── Model Config (icons, colors, descriptions) ───────────────────────────────

const MODEL_CONFIG: Record<string, {
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  borderColor: string;
  description: string;
  badge: string;
}> = {
  "risk-scoring-ai": {
    icon: <ShieldCheck className="h-5 w-5" />,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/25",
    description: "XGBoost risk classification engine scoring threat priority from 0–10",
    badge: "RISK ENGINE",
  },
  "noise-reduction-ai": {
    icon: <Filter className="h-5 w-5" />,
    color: "text-sky-400",
    bgColor: "bg-sky-500/10",
    borderColor: "border-sky-500/25",
    description: "Clustering and suppression model to reduce analyst alert fatigue",
    badge: "NOISE FILTER",
  },
  "playbook-recommendation-ai": {
    icon: <BookOpen className="h-5 w-5" />,
    color: "text-violet-400",
    bgColor: "bg-violet-500/10",
    borderColor: "border-violet-500/25",
    description: "Recommends optimal response playbooks based on threat context",
    badge: "PLAYBOOK AI",
  },
  "patch-recommendation-ai": {
    icon: <Wrench className="h-5 w-5" />,
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/25",
    description: "CVE-aware patch prioritization engine using EPSS and CVSS scores",
    badge: "PATCH AI",
  },
  "phishing-detection-ai": {
    icon: <Mail className="h-5 w-5" />,
    color: "text-rose-400",
    bgColor: "bg-rose-500/10",
    borderColor: "border-rose-500/25",
    description: "NLP-powered email threat detection with confidence scoring",
    badge: "PHISHING AI",
  },
  "llm-investigation-assistant": {
    icon: <MessageSquare className="h-5 w-5" />,
    color: "text-indigo-400",
    bgColor: "bg-indigo-500/10",
    borderColor: "border-indigo-500/25",
    description: "GPT-based investigation assistant for automated incident narratives",
    badge: "LLM ASSIST",
  },
};

const API_BASE = "http://0.0.0.0:8000/api/v1";
const WS_URL = "ws://0.0.0.0:8000/api/v1/ai-ops/ws";

// ─── Hooks ────────────────────────────────────────────────────────────────────

function useAiOverview() {
  const [data, setData] = useState<AiOverviewData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetch_ = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/ai-ops/models`);
      if (res.ok) setData(await res.json());
    } catch { /* silently fall through to fallback */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetch_(); }, [fetch_]);
  return { data, loading, refetch: fetch_ };
}

function useModelTelemetry(modelId: string | null) {
  const [telemetry, setTelemetry] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!modelId) { setTelemetry(null); return; }
    setLoading(true);
    fetch(`${API_BASE}/ai-ops/models/${modelId}/telemetry`)
      .then(r => r.json())
      .then(setTelemetry)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [modelId]);

  return { telemetry, loading };
}

function useLiveEvents(maxEvents = 40) {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connect = () => {
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;
        ws.onopen = () => setConnected(true);
        ws.onmessage = (e) => {
          try {
            const payload: LiveEvent = JSON.parse(e.data);
            setEvents(prev => [payload, ...prev].slice(0, maxEvents));
          } catch { /* ignore malformed */ }
        };
        ws.onclose = () => {
          setConnected(false);
          setTimeout(connect, 3000); // exponential backoff reconnect
        };
        ws.onerror = () => ws.close();
      } catch { /* ignore */ }
    };
    connect();
    return () => { wsRef.current?.close(); };
  }, [maxEvents]);

  const sendPing = useCallback(() => { wsRef.current?.send("ping"); }, []);
  return { events, connected, sendPing };
}

// ─── Sub-components ───────────────────────────────────────────────────────────

const TOOLTIP_STYLE = {
  backgroundColor: "rgba(11,18,32,0.95)",
  backdropFilter: "blur(12px)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: "12px",
  color: "#f8fafc",
  fontSize: "11px",
};

function HealthDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    online: "bg-emerald-400",
    warning: "bg-amber-400",
    degraded: "bg-rose-400",
    offline: "bg-slate-500",
  };
  return (
    <span className="relative flex h-2 w-2">
      <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${colors[status] ?? "bg-slate-500"}`} />
      <span className={`relative inline-flex rounded-full h-2 w-2 ${colors[status] ?? "bg-slate-500"}`} />
    </span>
  );
}

function DriftMeter({ score }: { score: number }) {
  const pct = Math.min(score * 100, 100);
  const color = pct > 20 ? "bg-rose-500" : pct > 10 ? "bg-amber-500" : "bg-emerald-500";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[9px] font-mono text-muted-foreground/60">
        <span>DRIFT</span>
        <span className={pct > 20 ? "text-rose-400" : pct > 10 ? "text-amber-400" : "text-emerald-400"}>
          {(score * 100).toFixed(1)}%
        </span>
      </div>
      <div className="h-1 w-full bg-muted/30 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={`h-full rounded-full ${color}`}
        />
      </div>
    </div>
  );
}

function MetricBar({ label, value, max = 1, color = "bg-primary" }: {
  label: string; value: number; max?: number; color?: string;
}) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-center">
        <span className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/60">{label}</span>
        <span className="text-[11px] font-mono font-bold text-foreground">
          {max === 1 ? `${(value * 100).toFixed(1)}%` : value.toLocaleString()}
        </span>
      </div>
      <div className="h-1.5 w-full bg-muted/30 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          className={`h-full rounded-full ${color}`}
        />
      </div>
    </div>
  );
}

// ─── Model Card ───────────────────────────────────────────────────────────────

function ModelCard({ model, liveEvents, onClick }: {
  model: ModelOverview;
  liveEvents: LiveEvent[];
  onClick: () => void;
}) {
  const cfg = MODEL_CONFIG[model.id] ?? {
    icon: <Cpu className="h-5 w-5" />,
    color: "text-primary",
    bgColor: "bg-primary/10",
    borderColor: "border-primary/25",
    description: "",
    badge: "AI MODEL",
  };

  const recentForModel = liveEvents.filter(e => e.model_id === model.id).slice(0, 5);
  const hasDriftAlert = recentForModel.some(e => e.drift_alert);

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      onClick={onClick}
      className={`group relative cursor-pointer rounded-2xl border bg-card/30 backdrop-blur-md p-5 transition-all duration-300
        hover:bg-card/50 hover:-translate-y-1 hover:shadow-2xl
        ${hasDriftAlert ? "border-amber-500/40 shadow-[0_0_20px_rgba(245,158,11,0.1)]" : "border-border/40 hover:border-primary/30"}`}
    >
      {/* Top gradient bar */}
      <div className={`absolute top-0 left-0 right-0 h-[2px] rounded-t-2xl ${cfg.bgColor} opacity-80`} />

      {/* Drift alert badge */}
      {hasDriftAlert && (
        <div className="absolute top-3 right-3">
          <Badge className="bg-amber-500/15 text-amber-400 border border-amber-500/30 text-[9px] px-1.5 py-0.5">
            <AlertTriangle className="h-2.5 w-2.5 mr-1" />DRIFT
          </Badge>
        </div>
      )}

      {/* Header row */}
      <div className="flex items-start gap-3 mb-4">
        <div className={`p-2.5 rounded-xl ${cfg.bgColor} border ${cfg.borderColor} ${cfg.color} shrink-0`}>
          {cfg.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <HealthDot status={model.health_status} />
            <p className="text-[9px] font-mono font-black uppercase tracking-[0.18em] text-muted-foreground/50">
              {cfg.badge}
            </p>
          </div>
          <h3 className="text-sm font-bold text-foreground leading-tight truncate">{model.model_name}</h3>
        </div>
      </div>

      {/* Accuracy big number */}
      <div className="mb-4">
        <p className="text-[9px] font-mono uppercase tracking-widest text-muted-foreground/50 mb-0.5">ACCURACY</p>
        <div className="flex items-baseline gap-1">
          <span className={`text-3xl font-black font-mono tabular-nums ${cfg.color}`}>
            {(model.accuracy * 100).toFixed(1)}
          </span>
          <span className="text-sm text-muted-foreground/50 font-mono">%</span>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <p className="text-[9px] font-mono uppercase text-muted-foreground/40">REQUESTS</p>
          <p className="text-sm font-bold font-mono">{model.request_count.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-[9px] font-mono uppercase text-muted-foreground/40">LAST RUN</p>
          <p className="text-sm font-bold font-mono">
            {new Date(model.last_execution).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </p>
        </div>
      </div>

      {/* Drift meter */}
      <DriftMeter score={model.drift_score} />

      {/* Live activity stream (last 3 events) */}
      {recentForModel.length > 0 && (
        <div className="mt-3 pt-3 border-t border-border/20 space-y-1">
          {recentForModel.slice(0, 2).map((ev, i) => (
            <div key={i} className="flex items-center gap-1.5 text-[10px] text-muted-foreground/50">
              <span className="h-1 w-1 rounded-full bg-emerald-500 shrink-0" />
              <span className="font-mono truncate">{ev.outcome.replace(/_/g, " ")}</span>
              <span className="ml-auto font-mono">{ev.latency.toFixed(2)}s</span>
            </div>
          ))}
        </div>
      )}

      {/* Click hint */}
      <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
        <ChevronRight className="h-4 w-4 text-muted-foreground/40" />
      </div>
    </motion.div>
  );
}

// ─── Detail Drawer ────────────────────────────────────────────────────────────

function ModelDetailDrawer({ model, telemetry, telLoading, onClose }: {
  model: ModelOverview;
  telemetry: any;
  telLoading: boolean;
  onClose: () => void;
}) {
  const cfg = MODEL_CONFIG[model.id];
  const PURPLE = "#8b5cf6"; const CYAN = "#22d3ee"; const EMERALD = "#10b981";
  const ROSE = "#f43f5e"; const AMBER = "#f59e0b"; const INDIGO = "#6366f1";

  // Helper to render the right telemetry panel per model
  const renderTelemetryContent = () => {
    if (telLoading) {
      return (
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-8 rounded-lg bg-muted/20 animate-pulse" />
          ))}
        </div>
      );
    }
    if (!telemetry) return <p className="text-muted-foreground/50 text-sm">No telemetry data available.</p>;

    if (model.id === "risk-scoring-ai" && telemetry.risk_scoring) {
      const rs = telemetry.risk_scoring;
      const distData = Object.entries(rs.confidence_distribution ?? {}).map(([k, v]) => ({
        range: k, count: v as number,
      }));
      const metricsRadar = [
        { subject: "Accuracy", value: rs.accuracy * 100 },
        { subject: "Precision", value: rs.precision * 100 },
        { subject: "Recall", value: rs.recall * 100 },
        { subject: "F1", value: rs.f1 * 100 },
        { subject: "ROC-AUC", value: rs.roc_auc * 100 },
      ];
      return (
        <div className="space-y-6">
          {/* Core metrics */}
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Precision", value: rs.precision, color: "text-emerald-400" },
              { label: "Recall", value: rs.recall, color: "text-sky-400" },
              { label: "F1 Score", value: rs.f1, color: "text-violet-400" },
              { label: "ROC-AUC", value: rs.roc_auc, color: "text-amber-400" },
            ].map(m => (
              <div key={m.label} className="bg-muted/10 rounded-xl p-3 border border-border/20">
                <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50 mb-1">{m.label}</p>
                <p className={`text-xl font-black font-mono ${m.color}`}>{(m.value * 100).toFixed(2)}%</p>
              </div>
            ))}
          </div>
          {/* FP / FN */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-rose-500/5 border border-rose-500/20 rounded-xl p-3">
              <p className="text-[9px] uppercase tracking-widest text-rose-400/60 mb-1">FALSE POSITIVES</p>
              <p className="text-xl font-black font-mono text-rose-400">{rs.false_positives.toLocaleString()}</p>
            </div>
            <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-3">
              <p className="text-[9px] uppercase tracking-widest text-amber-400/60 mb-1">FALSE NEGATIVES</p>
              <p className="text-xl font-black font-mono text-amber-400">{rs.false_negatives.toLocaleString()}</p>
            </div>
          </div>
          {/* Radar */}
          <div>
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground/50 mb-3">PERFORMANCE RADAR</p>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={metricsRadar}>
                  <PolarGrid stroke="rgba(255,255,255,0.06)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 9, fill: "#64748b" }} />
                  <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 8, fill: "#64748b" }} />
                  <Radar dataKey="value" stroke={EMERALD} fill={EMERALD} fillOpacity={0.15} strokeWidth={2} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: any) => `${Number(v).toFixed(1)}%`} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
          {/* Confidence Distribution */}
          <div>
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground/50 mb-3">CONFIDENCE DISTRIBUTION</p>
            <div className="h-40">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distData} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                  <XAxis dataKey="range" tick={{ fontSize: 8, fill: "#64748b" }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fontSize: 8, fill: "#64748b" }} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Bar dataKey="count" fill={EMERALD} radius={[3, 3, 0, 0]} opacity={0.8} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      );
    }

    if (model.id === "noise-reduction-ai" && telemetry.noise_reduction) {
      const nr = telemetry.noise_reduction;
      const pieData = [
        { name: "Suppressed", value: nr.alerts_suppressed, fill: CYAN },
        { name: "Duplicates", value: nr.duplicates_removed, fill: PURPLE },
        { name: "Passed", value: nr.alerts_received - nr.alerts_suppressed - nr.duplicates_removed, fill: EMERALD },
      ].filter(d => d.value > 0);
      return (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Alerts Received", value: nr.alerts_received.toLocaleString(), color: "text-foreground" },
              { label: "Alerts Suppressed", value: nr.alerts_suppressed.toLocaleString(), color: "text-sky-400" },
              { label: "Duplicates Removed", value: nr.duplicates_removed.toLocaleString(), color: "text-violet-400" },
              { label: "Clusters Generated", value: nr.clusters_generated.toLocaleString(), color: "text-amber-400" },
            ].map(m => (
              <div key={m.label} className="bg-muted/10 rounded-xl p-3 border border-border/20">
                <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50 mb-1">{m.label}</p>
                <p className={`text-xl font-black font-mono ${m.color}`}>{m.value}</p>
              </div>
            ))}
          </div>
          <div className="bg-sky-500/5 border border-sky-500/20 rounded-xl p-4 text-center">
            <p className="text-[10px] uppercase tracking-widest text-sky-400/60 mb-1">REDUCTION EFFICIENCY</p>
            <p className="text-4xl font-black font-mono text-sky-400">{nr.reduction_percentage.toFixed(1)}%</p>
            <p className="text-xs text-muted-foreground/40 mt-1">Alert noise eliminated</p>
          </div>
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                  dataKey="value" nameKey="name" paddingAngle={3} strokeWidth={0}>
                  {pieData.map((d, i) => <Cell key={i} fill={d.fill} opacity={0.85} />)}
                </Pie>
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend iconSize={8} wrapperStyle={{ fontSize: "10px", color: "#64748b" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      );
    }

    if (model.id === "playbook-recommendation-ai" && telemetry.playbook_recommendation) {
      const pb = telemetry.playbook_recommendation;
      return (
        <div className="space-y-5">
          <div className="grid grid-cols-1 gap-3">
            <MetricBar label="Recommendation Accuracy" value={pb.recommendation_accuracy} color="bg-violet-500" />
            <MetricBar label="Success Rate" value={pb.success_rate / 100} color="bg-emerald-500" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-3">
              <p className="text-[9px] uppercase tracking-widest text-amber-400/60 mb-1">OVERRIDE RATE</p>
              <p className="text-xl font-black font-mono text-amber-400">{pb.analyst_override_rate.toFixed(2)}%</p>
              <p className="text-[9px] text-muted-foreground/40 mt-1">Analyst disagreement</p>
            </div>
            <div className="bg-violet-500/5 border border-violet-500/20 rounded-xl p-3">
              <p className="text-[9px] uppercase tracking-widest text-violet-400/60 mb-1">AVG EXEC TIME</p>
              <p className="text-xl font-black font-mono text-violet-400">{pb.average_execution_time.toFixed(3)}s</p>
              <p className="text-[9px] text-muted-foreground/40 mt-1">Recommendation latency</p>
            </div>
          </div>
          {/* Override vs success bar chart */}
          <div>
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground/50 mb-3">SUCCESS vs OVERRIDE</p>
            <div className="h-36">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={[
                  { name: "Success", value: pb.success_rate, fill: EMERALD },
                  { name: "Override", value: pb.analyst_override_rate, fill: AMBER },
                  { name: "Accuracy", value: pb.recommendation_accuracy * 100, fill: PURPLE },
                ]} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 9, fill: "#64748b" }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fontSize: 9, fill: "#64748b" }} tickLine={false} axisLine={false} domain={[0, 100]} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: any) => `${Number(v).toFixed(1)}%`} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]} barSize={32}>
                    {[EMERALD, AMBER, PURPLE].map((c, i) => <Cell key={i} fill={c} opacity={0.85} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      );
    }

    if (model.id === "patch-recommendation-ai" && telemetry.patch_recommendation) {
      const pa = telemetry.patch_recommendation;
      const acceptRate = pa.recommendations_generated > 0
        ? ((pa.accepted_recommendations / pa.recommendations_generated) * 100).toFixed(1) : "0";
      return (
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Generated", value: pa.recommendations_generated.toLocaleString(), color: "text-foreground" },
              { label: "Accepted", value: pa.accepted_recommendations.toLocaleString(), color: "text-emerald-400" },
              { label: "Ignored", value: pa.ignored_recommendations.toLocaleString(), color: "text-rose-400" },
              { label: "Accept Rate", value: `${acceptRate}%`, color: "text-amber-400" },
            ].map(m => (
              <div key={m.label} className="bg-muted/10 rounded-xl p-3 border border-border/20">
                <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50 mb-1">{m.label}</p>
                <p className={`text-xl font-black font-mono ${m.color}`}>{m.value}</p>
              </div>
            ))}
          </div>
          <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4">
            <p className="text-[10px] uppercase tracking-widest text-amber-400/60 mb-1">EXPOSURE REDUCTION SCORE</p>
            <div className="flex items-baseline gap-2">
              <p className="text-4xl font-black font-mono text-amber-400">{pa.exposure_reduction_score.toFixed(1)}</p>
              <span className="text-lg text-amber-400/60 font-mono">/ 100</span>
            </div>
            <div className="mt-2 h-2 w-full bg-muted/30 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-amber-500 to-amber-300 rounded-full"
                style={{ width: `${pa.exposure_reduction_score}%` }} />
            </div>
          </div>
          <div className="h-36">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={[
                  { name: "Accepted", value: pa.accepted_recommendations, fill: EMERALD },
                  { name: "Ignored", value: pa.ignored_recommendations, fill: ROSE },
                ]} cx="50%" cy="50%" innerRadius={45} outerRadius={72}
                  dataKey="value" nameKey="name" paddingAngle={4} strokeWidth={0}>
                  <Cell fill={EMERALD} opacity={0.85} />
                  <Cell fill={ROSE} opacity={0.85} />
                </Pie>
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend iconSize={8} wrapperStyle={{ fontSize: "10px", color: "#64748b" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      );
    }

    if (model.id === "phishing-detection-ai" && telemetry.phishing_detection) {
      const ph = telemetry.phishing_detection;
      const distData = Object.entries(ph.confidence_distribution ?? {}).map(([k, v]) => ({ range: k, count: v as number }));
      return (
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Emails Analyzed", value: ph.emails_analyzed.toLocaleString(), color: "text-foreground" },
              { label: "Phishing Detected", value: ph.phishing_detected.toLocaleString(), color: "text-rose-400" },
              { label: "False Positives", value: ph.false_positives.toLocaleString(), color: "text-amber-400" },
              { label: "Detection Rate",
                value: `${ph.emails_analyzed > 0 ? ((ph.phishing_detected / ph.emails_analyzed) * 100).toFixed(2) : 0}%`,
                color: "text-sky-400" },
            ].map(m => (
              <div key={m.label} className="bg-muted/10 rounded-xl p-3 border border-border/20">
                <p className="text-[9px] uppercase tracking-widest text-muted-foreground/50 mb-1">{m.label}</p>
                <p className={`text-xl font-black font-mono ${m.color}`}>{m.value}</p>
              </div>
            ))}
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground/50 mb-3">CONFIDENCE DISTRIBUTION</p>
            <div className="h-44">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distData} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                  <XAxis dataKey="range" tick={{ fontSize: 8, fill: "#64748b" }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fontSize: 8, fill: "#64748b" }} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Bar dataKey="count" radius={[3, 3, 0, 0]}>
                    {distData.map((_, i) => <Cell key={i} fill={i >= distData.length - 2 ? ROSE : "#475569"} opacity={0.85} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      );
    }

    if (model.id === "llm-investigation-assistant" && telemetry.llm_investigation) {
      const llm = telemetry.llm_investigation;
      const tokenData = [
        { name: "Prompt", value: llm.prompt_tokens, fill: INDIGO },
        { name: "Completion", value: llm.completion_tokens, fill: CYAN },
      ];
      const starCount = Math.round(llm.analyst_feedback_score);
      return (
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2 bg-indigo-500/5 border border-indigo-500/20 rounded-xl p-4">
              <p className="text-[9px] uppercase tracking-widest text-indigo-400/60 mb-1">TOTAL TOKEN USAGE</p>
              <p className="text-3xl font-black font-mono text-indigo-400">{llm.token_usage.toLocaleString()}</p>
            </div>
            {[
              { label: "Requests", value: llm.request_count.toLocaleString(), color: "text-foreground", icon: <BarChart2 className="h-3 w-3" /> },
              { label: "Avg Latency", value: `${llm.latency.toFixed(2)}s`, color: "text-sky-400", icon: <Clock className="h-3 w-3" /> },
              { label: "Est. Cost", value: `$${llm.estimated_cost.toFixed(2)}`, color: "text-emerald-400", icon: <DollarSign className="h-3 w-3" /> },
              { label: "Feedback", value: `${llm.analyst_feedback_score.toFixed(2)} / 5`, color: "text-amber-400", icon: <Star className="h-3 w-3" /> },
            ].map(m => (
              <div key={m.label} className="bg-muted/10 rounded-xl p-3 border border-border/20">
                <div className="flex items-center gap-1 text-muted-foreground/50 mb-1">
                  {m.icon}
                  <p className="text-[9px] uppercase tracking-widest">{m.label}</p>
                </div>
                <p className={`text-lg font-black font-mono ${m.color}`}>{m.value}</p>
              </div>
            ))}
          </div>
          {/* Star rating */}
          <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-3">
            <p className="text-[9px] uppercase tracking-widest text-amber-400/60 mb-2">ANALYST FEEDBACK SCORE</p>
            <div className="flex gap-1">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className={`h-5 w-5 ${i < starCount ? "fill-amber-400 text-amber-400" : "text-muted-foreground/20"}`} />
              ))}
              <span className="ml-2 text-lg font-black font-mono text-amber-400">{llm.analyst_feedback_score.toFixed(2)}</span>
            </div>
          </div>
          {/* Token breakdown */}
          <div>
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground/50 mb-3">TOKEN BREAKDOWN</p>
            <div className="h-36">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={tokenData} cx="50%" cy="50%" innerRadius={40} outerRadius={65}
                    dataKey="value" nameKey="name" paddingAngle={3} strokeWidth={0}>
                    {tokenData.map((d, i) => <Cell key={i} fill={d.fill} opacity={0.85} />)}
                  </Pie>
                  <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: any) => Number(v).toLocaleString()} />
                  <Legend iconSize={8} wrapperStyle={{ fontSize: "10px", color: "#64748b" }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      );
    }

    return <p className="text-muted-foreground/50 text-sm">No telemetry available for this model.</p>;
  };

  return (
    <motion.div
      initial={{ x: "100%", opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: "100%", opacity: 0 }}
      transition={{ type: "spring", damping: 28, stiffness: 280 }}
      className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-[hsl(var(--background))] border-l border-border/50 shadow-2xl flex flex-col"
    >
      {/* Drawer header */}
      <div className={`flex items-center gap-3 px-6 py-5 border-b border-border/30 ${cfg?.bgColor ?? ""}`}>
        <div className={`p-2.5 rounded-xl ${cfg?.bgColor} border ${cfg?.borderColor} ${cfg?.color}`}>
          {cfg?.icon}
        </div>
        <div className="flex-1">
          <p className="text-[9px] font-mono uppercase tracking-widest text-muted-foreground/50">{cfg?.badge}</p>
          <h2 className="text-base font-bold">{model.model_name}</h2>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8 rounded-lg hover:bg-muted/30">
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Status row */}
      <div className="flex items-center gap-4 px-6 py-3 border-b border-border/20 bg-muted/5">
        <div className="flex items-center gap-2">
          <HealthDot status={model.health_status} />
          <span className="text-xs capitalize font-mono text-muted-foreground">{model.health_status}</span>
        </div>
        <Separator orientation="vertical" className="h-4" />
        <span className="text-xs font-mono text-muted-foreground">{model.request_count.toLocaleString()} requests</span>
        <Separator orientation="vertical" className="h-4" />
        <span className={`text-xs font-mono font-bold ${cfg?.color}`}>{(model.accuracy * 100).toFixed(1)}% accuracy</span>
      </div>

      {/* Description */}
      <div className="px-6 py-3 bg-muted/5 border-b border-border/20">
        <p className="text-xs text-muted-foreground/70 leading-relaxed">{cfg?.description}</p>
      </div>

      {/* Telemetry content */}
      <ScrollArea className="flex-1 px-6 py-5">
        {renderTelemetryContent()}
      </ScrollArea>
    </motion.div>
  );
}

// ─── Live Stream Feed ─────────────────────────────────────────────────────────

function LiveFeed({ events, connected }: { events: LiveEvent[]; connected: boolean }) {
  const cfg = (id: string) => MODEL_CONFIG[id];
  return (
    <Card className="bg-card/20 border-border/40 backdrop-blur-md flex flex-col">
      <CardHeader className="border-b border-border/30 pb-3 pt-4 px-5">
        <CardTitle className="text-sm font-bold flex items-center gap-2">
          <Activity className={`h-3.5 w-3.5 ${connected ? "text-emerald-400 animate-pulse" : "text-muted-foreground/40"}`} />
          Live Execution Stream
          {connected
            ? <Badge className="ml-auto bg-emerald-500/10 text-emerald-400 border-emerald-500/20 text-[9px]">LIVE</Badge>
            : <Badge className="ml-auto bg-muted/20 text-muted-foreground/40 border-muted/20 text-[9px]">OFFLINE</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0 flex-1">
        <ScrollArea className="h-[340px]">
          {events.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full py-12 text-muted-foreground/30">
              <Zap className="h-8 w-8 mb-2" />
              <p className="text-xs">Waiting for events…</p>
            </div>
          ) : (
            <div className="p-3 space-y-1.5">
              <AnimatePresence initial={false}>
                {events.map((ev, i) => {
                  const c = cfg(ev.model_id);
                  return (
                    <motion.div
                      key={`${ev.event_id}-${i}`}
                      initial={{ opacity: 0, x: 12 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.25 }}
                      className={`flex items-center gap-2.5 p-2.5 rounded-lg border text-[10px]
                        ${ev.drift_alert ? "border-amber-500/25 bg-amber-500/5" : "border-border/20 bg-muted/5"}`}
                    >
                      <span className={`shrink-0 ${c?.color ?? "text-primary"}`}>{c?.icon}</span>
                      <div className="flex-1 min-w-0">
                        <span className="font-mono font-bold text-foreground/80 truncate block">
                          {ev.outcome.replace(/_/g, " ")}
                        </span>
                        <span className="text-muted-foreground/40 font-mono">
                          {ev.model_id.replace(/-ai$/, "").replace(/-/g, " ")}
                        </span>
                      </div>
                      {ev.drift_alert && <AlertTriangle className="h-3 w-3 text-amber-400 shrink-0" />}
                      {ev.confidence && (
                        <span className="font-mono text-muted-foreground/50">{(ev.confidence * 100).toFixed(0)}%</span>
                      )}
                      <span className="font-mono text-muted-foreground/40 shrink-0">{ev.latency.toFixed(2)}s</span>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

// ─── Main Page Component ──────────────────────────────────────────────────────

export default function AiOperationsPage() {
  const { data, loading, refetch } = useAiOverview();
  const { events, connected } = useLiveEvents();
  const [selectedModel, setSelectedModel] = useState<ModelOverview | null>(null);
  const { telemetry, loading: telLoading } = useModelTelemetry(selectedModel?.id ?? null);

  const systemStatusColor = (s?: string) => {
    if (s === "healthy") return "text-emerald-400 bg-emerald-500/10 border-emerald-500/25";
    if (s === "warning") return "text-amber-400 bg-amber-500/10 border-amber-500/25";
    return "text-rose-400 bg-rose-500/10 border-rose-500/25";
  };

  return (
    <div className="w-full h-full space-y-8 pb-20">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <PageHeader
          title="AI Operations Center"
          description="Real-time telemetry, drift monitoring, and analyst feedback for all 6 intelligence models"
          breadcrumbs={[{ label: "AI" }, { label: "AI Operations Center" }]}
        />
        <div className="flex items-center gap-3 shrink-0">
          {data && (
            <Badge className={`border text-[10px] px-3 py-1 font-mono font-bold uppercase ${systemStatusColor(data.system_status)}`}>
              <Circle className="h-2 w-2 mr-1.5 fill-current" />
              {data.system_status}
            </Badge>
          )}
          <Button variant="outline" size="sm" onClick={refetch}
            className="font-mono text-xs border-border/40 gap-2 hover:bg-primary/5">
            <RefreshCw className="h-3.5 w-3.5" /> Sync Models
          </Button>
        </div>
      </div>

      {/* Top KPIs */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 rounded-2xl bg-muted/10 border border-border/20 animate-pulse" />
          ))}
        </div>
      ) : data && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Total Executions", value: data.total_executions.toLocaleString(), icon: <Cpu />, color: "text-primary", bg: "bg-primary/10", border: "border-primary/20" },
            { label: "Avg Drift Score", value: `${(data.average_drift * 100).toFixed(2)}%`, icon: <TrendingUp />, color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" },
            { label: "Active Models", value: `${data.models.filter(m => m.health_status === "online").length} / ${data.models.length}`, icon: <Brain />, color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
            { label: "Live Events", value: connected ? `${events.length}` : "Offline", icon: <Activity />, color: connected ? "text-sky-400" : "text-muted-foreground/40", bg: "bg-sky-500/10", border: "border-sky-500/20" },
          ].map((kpi, i) => (
            <CyberCard key={kpi.label} delay={i * 0.06} className="bg-card/20 border-border/40">
              <div className="flex justify-between items-start mb-3">
                <div className={`p-2.5 rounded-xl ${kpi.bg} border ${kpi.border} ${kpi.color}`}>
                  {React.cloneElement(kpi.icon as React.ReactElement, { className: "h-4 w-4" })}
                </div>
              </div>
              <p className="text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground/50 mb-1">{kpi.label}</p>
              <p className={`text-2xl font-black font-mono ${kpi.color}`}>{kpi.value}</p>
            </CyberCard>
          ))}
        </div>
      )}

      {/* Models Grid + Live Feed */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Models 2×3 grid */}
        <div className="xl:col-span-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {loading
            ? [...Array(6)].map((_, i) => (
                <div key={i} className="h-72 rounded-2xl bg-muted/10 border border-border/20 animate-pulse" />
              ))
            : (data?.models ?? []).map(model => (
                <ModelCard
                  key={model.id}
                  model={model}
                  liveEvents={events}
                  onClick={() => setSelectedModel(model)}
                />
              ))
          }
        </div>

        {/* Live Feed sidebar */}
        <div className="xl:col-span-1">
          <LiveFeed events={events} connected={connected} />
        </div>
      </div>

      {/* Model Detail Drawer */}
      <AnimatePresence>
        {selectedModel && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedModel(null)}
              className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
            />
            <ModelDetailDrawer
              model={selectedModel}
              telemetry={telemetry}
              telLoading={telLoading}
              onClose={() => setSelectedModel(null)}
            />
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
