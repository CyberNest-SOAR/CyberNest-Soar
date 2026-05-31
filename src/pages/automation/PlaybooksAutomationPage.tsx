import { useState, useMemo, useCallback } from "react";
import { useDashboardData } from "@/hooks/useDashboardData";
import { PageHeader } from "@/components/PageHeader";
import { CyberCard } from "@/components/CyberCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  SlidersHorizontal, Workflow, CheckCircle2, RefreshCw, ShieldAlert,
  Activity, Cpu, Ban, ShieldOff, Clock, Plus, Trash2, Play, Zap,
  UserCheck, UserX,
} from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell } from "recharts";
import { toast } from "sonner";
import { ConfirmActionDialog } from "@/components/ConfirmActionDialog";
import type { PlaybookRule } from "@/types/playbook";

interface ApprovalItem {
  id: string;
  rule: string;
  alert_id: string;
  target: string;
  action: string;
  requested_by?: string;
  reason?: string;
  requested_at: string;
  priority?: string;
  status?: string;
  executed_at?: string;
  result?: string;
}

interface BlockedItem {
  id: string;
  type: "ip" | "hash" | "domain";
  value: string;
  reason: string;
  blocked_by: string;
  ticket_id: string;
  blocked_at: Date;
  expires_at: Date;
}

interface PlaybooksAutomationData {
  page: string;
  playbook_library: { rules: PlaybookRule[]; default_action: string; total_rules: number };
  execution_history: { outcomes: Record<string, number>; total_executions: number };
  simulation_mode: { available: boolean; endpoint: string };
  approval_workflows: { manual_approval_required: ApprovalItem[]; semi_automated: ApprovalItem[]; fully_automated: ApprovalItem[] };
}

const FALLBACK: PlaybooksAutomationData = {
  page: "Playbooks & Automation",
  playbook_library: { rules: [], default_action: "log_event", total_rules: 0 },
  execution_history: { outcomes: {}, total_executions: 0 },
  simulation_mode: { available: false, endpoint: "" },
  approval_workflows: { manual_approval_required: [], semi_automated: [], fully_automated: [] },
};

const API_BASE = "http://0.0.0.0:8000/api/v1";
const CHART_COLORS = [
  "hsl(var(--cyber-blue))", "hsl(var(--critical))", "hsl(var(--warning))",
  "hsl(var(--primary))", "hsl(var(--destructive))", "hsl(var(--secondary))",
  "hsl(var(--success))", "hsl(var(--accent))", "hsl(var(--info))",
];

/* ─── Add Block Modal ──────────────────────────────────────────────────── */

function AddBlockModal({ open, onClose, onAdd }: { open: boolean; onClose: () => void; onAdd: (b: BlockedItem) => void }) {
  const [type, setType] = useState<"ip" | "hash" | "domain">("ip");
  const [value, setValue] = useState("");
  const [reason, setReason] = useState("");
  const [ticketId, setTicketId] = useState("");
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-[hsl(var(--background))] border border-border/40 rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="px-6 py-4 border-b border-border/30">
          <h3 className="text-lg font-bold">Manually Block Item</h3>
          <p className="text-xs text-muted-foreground/60">Add an IP, hash, or domain to the blocklist</p>
        </div>
        <div className="px-6 py-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Type</label>
              <select value={type} onChange={e => setType(e.target.value as any)}
                className="w-full bg-background/50 border border-border/30 text-xs px-3 py-2 rounded-lg text-foreground focus:ring-1 focus:ring-primary outline-none">
                <option value="ip">IP Address</option><option value="hash">File Hash</option><option value="domain">Domain</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Value</label>
              <Input value={value} onChange={e => setValue(e.target.value)} placeholder={type === "ip" ? "192.168.1.100" : type === "hash" ? "sha256..." : "evil.com"} className="bg-background/50 border-border/30 text-xs font-mono" />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Reason</label>
            <Input value={reason} onChange={e => setReason(e.target.value)} placeholder="Why is this being blocked?" className="bg-background/50 border-border/30 text-xs" />
          </div>
          <div className="space-y-2">
            <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Ticket ID (optional)</label>
            <Input value={ticketId} onChange={e => setTicketId(e.target.value)} placeholder="INC-2026-XXXX" className="bg-background/50 border-border/30 text-xs font-mono" />
          </div>
        </div>
        <div className="px-6 py-4 border-t border-border/30 flex justify-end gap-3">
          <Button variant="outline" size="sm" onClick={onClose}>Cancel</Button>
          <Button size="sm" onClick={() => {
            if (!value || !reason) { toast.error("Value and reason are required"); return; }
            onAdd({
              id: `blk-${Date.now().toString(36)}`, type, value, reason,
              blocked_by: "manual", ticket_id: ticketId || "N/A",
              blocked_at: new Date(), expires_at: new Date(Date.now() + 86400000 * 30),
            });
            onClose();
            setValue(""); setReason(""); setTicketId("");
          }} disabled={!value || !reason}>
            <Ban className="h-3.5 w-3.5 mr-1.5" /> Add Block
          </Button>
        </div>
      </div>
    </div>
  );
}

/* ─── Simulation Dialog ─────────────────────────────────────────────────── */

function SimulationDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [severity, setSeverity] = useState("8");
  const [riskScore, setRiskScore] = useState("60");
  const [tags, setTags] = useState("malware, c2");
  const [result, setResult] = useState<any>(null);
  const [running, setRunning] = useState(false);

  const runSim = useCallback(async () => {
    setRunning(true);
    setResult(null);
    const payload = {
      severity: parseInt(severity) || 0,
      risk_score: parseInt(riskScore) || 0,
      tags: tags.split(",").map(t => t.trim()).filter(Boolean),
      description: "Simulated alert for playbook evaluation",
    };
    try {
      const resp = await fetch(`${API_BASE}/playbook-config/evaluate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (resp.ok) {
        const data = await resp.json();
        setResult(data);
        toast.success("Simulation Complete", { description: `Matched rule: ${data.matched_rule}` });
      } else {
        throw new Error(`API returned ${resp.status}`);
      }
    } catch {
      const mockRules = [
        { name: "critical_threat", minRisk: 80, minSev: 12, tags: ["c2", "misp_hit"], action: "isolate_host" },
        { name: "ransomware_detection", minRisk: 90, minSev: 14, tags: ["ransomware"], action: "full_remediation" },
        { name: "high_risk_activity", minRisk: 60, minSev: 8, tags: ["malware", "brute_force"], action: "block_ip" },
      ];
      const pTags = tags.split(",").map(t => t.trim().toLowerCase());
      const pRisk = parseInt(riskScore) || 0;
      const pSev = parseInt(severity) || 0;
      const matched = mockRules.find(r =>
        pRisk >= r.minRisk && pSev >= r.minSev &&
        (!r.tags.length || r.tags.some(t => pTags.includes(t)))
      );
      if (matched) {
        setResult({ matched_rule: matched.name, action: matched.action, confidence: 0.92, automation_level: "full", reason: `Simulated ${matched.name} match.` });
      } else {
        setResult({ matched_rule: "default", action: "log_event", confidence: 0.5, automation_level: "manual", reason: "No rules matched." });
      }
    } finally {
      setRunning(false);
    }
  }, [severity, riskScore, tags]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-[hsl(var(--background))] border border-border/40 rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="px-6 py-4 border-b border-border/30 flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"><Zap className="h-4 w-4" /></div>
          <div><h3 className="text-lg font-bold">Playbook Simulation</h3><p className="text-xs text-muted-foreground/60">Evaluate an alert against the rules engine</p></div>
        </div>
        <div className="px-6 py-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Severity</label>
              <Input value={severity} onChange={e => setSeverity(e.target.value)} className="bg-background/50 border-border/30 text-xs font-mono" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Risk Score</label>
              <Input value={riskScore} onChange={e => setRiskScore(e.target.value)} className="bg-background/50 border-border/30 text-xs font-mono" />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Tags</label>
            <Input value={tags} onChange={e => setTags(e.target.value)} placeholder="malware, c2" className="bg-background/50 border-border/30 text-xs font-mono" />
          </div>
          <Button onClick={runSim} disabled={running} className="w-full gap-2">
            {running ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {running ? "Evaluating..." : "Run Simulation"}
          </Button>
          {result && (
            <div className="bg-muted/10 rounded-xl p-4 border border-border/20 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Matched Rule</span>
                <Badge className={result.matched_rule === "default" ? "bg-muted/30 text-muted-foreground" : "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"}>{result.matched_rule}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Action</span>
                <span className="text-sm font-bold font-mono text-foreground/80">{result.action?.replace(/_/g, " ").toUpperCase()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Confidence</span>
                <span className="text-sm font-bold font-mono text-emerald-400">{(result.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Automation</span>
                <Badge variant="outline" className={result.automation_level === "full" ? "text-emerald-400" : result.automation_level === "semi" ? "text-amber-400" : "text-primary"}>{result.automation_level?.toUpperCase()}</Badge>
              </div>
              <p className="text-xs text-muted-foreground/70 mt-2 p-2 bg-black/20 rounded-lg">{result.reason}</p>
            </div>
          )}
        </div>
        <div className="px-6 py-4 border-t border-border/30 flex justify-end">
          <Button variant="outline" size="sm" onClick={onClose}>Close</Button>
        </div>
      </div>
    </div>
  );
}

/* ─── Main Page ─────────────────────────────────────────────────────────── */

export default function PlaybooksAutomationPage() {
  const { data, loading, refetch } = useDashboardData<PlaybooksAutomationData>("playbooks-automation.json", FALLBACK);
  const [showSimulation, setShowSimulation] = useState(false);
  const [showAddBlock, setShowAddBlock] = useState(false);
  const [confirmRelease, setConfirmRelease] = useState<BlockedItem | null>(null);

  const [blockedItems, setBlockedItems] = useState<BlockedItem[]>([
    { id: "blk-001", type: "ip", value: "185.220.101.45", reason: "C2 communication detected", blocked_by: "playbook-ai", ticket_id: "INC-2026-0082", blocked_at: new Date(), expires_at: new Date(Date.now() + 86400000 * 7) },
    { id: "blk-002", type: "ip", value: "91.121.87.34", reason: "Brute force attack source", blocked_by: "asmith", ticket_id: "INC-2026-0079", blocked_at: new Date(), expires_at: new Date(Date.now() + 86400000 * 3) },
    { id: "blk-003", type: "hash", value: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", reason: "Ransomware binary hash", blocked_by: "playbook-ai", ticket_id: "INC-2026-0075", blocked_at: new Date(), expires_at: new Date(Date.now() + 86400000 * 30) },
  ]);
  const [manualApprovals, setManualApprovals] = useState<ApprovalItem[]>([]);
  const [semiAutomated, setSemiAutomated] = useState<ApprovalItem[]>([]);
  const [fullyAutomated, setFullyAutomated] = useState<ApprovalItem[]>([]);

  useMemo(() => {
    if (data?.approval_workflows?.manual_approval_required) setManualApprovals(data.approval_workflows.manual_approval_required);
    if (data?.approval_workflows?.semi_automated) setSemiAutomated(data.approval_workflows.semi_automated);
    if (data?.approval_workflows?.fully_automated) setFullyAutomated(data.approval_workflows.fully_automated);
  }, [data]);

  const history = data?.execution_history ?? FALLBACK.execution_history;
  const simulation = data?.simulation_mode ?? FALLBACK.simulation_mode;

  const approveAction = useCallback((item: ApprovalItem, approved: boolean) => {
    setManualApprovals(prev => prev.filter(a => a.id !== item.id));
    if (approved) {
      setBlockedItems(prev => [...prev, {
        id: `blk-${Date.now().toString(36)}`,
        type: "ip",
        value: item.target,
        reason: item.reason || "Approved by analyst",
        blocked_by: "analyst",
        ticket_id: item.alert_id,
        blocked_at: new Date(),
        expires_at: new Date(Date.now() + 86400000 * 7),
      }]);
      toast.success("Action Approved", { description: `${item.action.replace(/_/g, " ")} on ${item.target} approved.` });
    } else {
      toast.success("Action Rejected", { description: `${item.action.replace(/_/g, " ")} on ${item.target} rejected.` });
    }
  }, []);

  const addBlock = useCallback((item: BlockedItem) => {
    setBlockedItems(prev => [item, ...prev]);
    toast.success("Item Blocked", { description: `${item.type.toUpperCase()} ${item.value} added to blocklist.` });
  }, []);

  const releaseBlock = useCallback(({ reason: r, ticketId }: { reason: string; ticketId: string }) => {
    if (!confirmRelease) return;
    setBlockedItems(prev => prev.filter(b => b.id !== confirmRelease.id));
    toast.success("Block Released", { description: `${confirmRelease.type.toUpperCase()} ${confirmRelease.value} released.` });
    setConfirmRelease(null);
  }, [confirmRelease]);

  const formatDate = (d: Date) => d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  const daysUntilExpiry = (d: Date) => Math.ceil((d.getTime() - Date.now()) / 86400000);

  const outcomesChartData = useMemo(() =>
    Object.entries(history.outcomes || {}).map(([key, val]) => ({
      name: key.replace(/_/g, " ").toUpperCase(), count: val,
    })).sort((a, b) => b.count - a.count), [history]);

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
          description="Approval workflows, blocklist management, playbook simulation, and execution outcomes"
          breadcrumbs={[{ label: "Automation" }, { label: "Playbooks & Automation" }]}
        />
        <div className="flex gap-3 bg-card/40 p-2 rounded-2xl border border-border/40 backdrop-blur-md">
          {simulation.available && (
            <Button variant="outline" size="sm" onClick={() => setShowSimulation(true)}
              className="font-mono text-xs border-emerald-500/20 bg-emerald-500/5 text-emerald-400 flex items-center gap-2 hover:bg-emerald-500/10">
              <Zap className="h-3.5 w-3.5" /> Simulate
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={refetch}
            className="font-mono text-xs border-border/40 flex items-center gap-2 hover:bg-primary/5">
            <RefreshCw className="h-3.5 w-3.5" /> Sync
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <CyberCard delay={0.05} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary"><Workflow className="h-5 w-5" /></div>
            <Badge className="bg-primary/10 text-primary border border-primary/20 text-[10px]">EXECUTIONS</Badge>
          </div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Total Playbook Runs</p>
          <h3 className="text-3xl font-black font-mono tracking-tight text-foreground">{history.total_executions?.toLocaleString()}</h3>
        </CyberCard>
        <CyberCard delay={0.1} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500"><CheckCircle2 className="h-5 w-5 animate-pulse" /></div>
            <Badge variant="outline" className="text-emerald-500 bg-emerald-500/5 border-emerald-500/20 text-[10px]">AUTO_BLOCK</Badge>
          </div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Automated Block Actions</p>
          <h3 className="text-3xl font-black font-mono tracking-tight text-emerald-500">{((history.outcomes?.automated_block || 0) + (history.outcomes?.ip_blocked || 0)).toLocaleString()}</h3>
        </CyberCard>
        <CyberCard delay={0.15} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500"><ShieldAlert className="h-5 w-5 animate-pulse" /></div>
            <Badge variant="outline" className="text-rose-500 bg-rose-500/5 border-rose-500/20 text-[10px]">PENDING</Badge>
          </div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Pending Approvals</p>
          <h3 className="text-3xl font-black font-mono tracking-tight text-rose-500">{manualApprovals.length}</h3>
        </CyberCard>
      </div>

      {/* Outcomes Chart + Approval Workflows */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold flex items-center gap-2">
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
                  <Tooltip contentStyle={{ backgroundColor: "rgba(0, 0, 0, 0.85)", backdropFilter: "blur(12px)", border: "1px solid hsl(var(--border) / 0.4)", borderRadius: "12px", color: "white" }} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} barSize={20}>
                    {outcomesChartData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Approval Workflows */}
        <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold flex items-center gap-2">
              <SlidersHorizontal className="h-4 w-4 text-primary" />
              Approval Workflows
            </CardTitle>
            <CardDescription>Pending actions requiring analyst intervention</CardDescription>
          </CardHeader>
          <CardContent className="pt-4 space-y-4">
            {manualApprovals.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground/40">
                <CheckCircle2 className="h-8 w-8 mx-auto mb-2 opacity-40" />
                <p className="text-xs font-mono">No pending approvals</p>
              </div>
            ) : (
              manualApprovals.slice(0, 3).map(item => (
                <div key={item.id} className={`rounded-xl border p-3.5 ${
                  item.priority === "critical"
                    ? "bg-rose-500/5 border-rose-500/25"
                    : "bg-amber-500/5 border-amber-500/25"
                }`}>
                  <div className="flex items-center justify-between mb-2">
                    <Badge className={item.priority === "critical" ? "bg-rose-500/15 text-rose-400 border-rose-500/30 text-[9px]" : "bg-amber-500/15 text-amber-400 border-amber-500/30 text-[9px]"}>
                      {item.priority?.toUpperCase()}
                    </Badge>
                    <span className="text-[9px] font-mono text-muted-foreground/50">{item.rule.replace(/_/g, " ")}</span>
                  </div>
                  <p className="text-xs font-bold font-mono text-foreground/80 truncate">{item.target}</p>
                  <p className="text-[9px] text-muted-foreground/60 mt-1 line-clamp-2">{item.reason}</p>
                  <div className="flex gap-2 mt-2">
                    <Button size="sm" variant="outline" onClick={() => approveAction(item, true)}
                      className="h-7 text-[9px] gap-1 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10">
                      <UserCheck className="h-3 w-3" /> Approve
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => approveAction(item, false)}
                      className="h-7 text-[9px] gap-1 text-rose-400 border-rose-500/30 hover:bg-rose-500/10">
                      <UserX className="h-3 w-3" /> Reject
                    </Button>
                  </div>
                </div>
              ))
            )}
            {manualApprovals.length > 3 && (
              <p className="text-[10px] text-muted-foreground/50 text-center font-mono">+{manualApprovals.length - 3} more pending</p>
            )}
            <div className="pt-2 border-t border-border/20">
              <div className="flex justify-between text-[10px] text-muted-foreground/50 font-mono">
                <span>Semi-automated: {semiAutomated.filter(s => s.status === "pending").length} pending</span>
                <span className="text-emerald-400">Auto: {fullyAutomated.filter(f => f.status === "completed").length} done</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Blocklist Registry */}
      <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
        <CardHeader className="border-b border-border/40 pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg font-bold flex items-center gap-2">
                <Ban className="h-4 w-4 text-rose-500" />
                Active Blocklist Registry
              </CardTitle>
              <CardDescription>Currently blocked IPs, hashes, and domains — add or release blocks</CardDescription>
            </div>
            <Button size="sm" variant="outline" onClick={() => setShowAddBlock(true)}>
              <Ban className="h-3.5 w-3.5 mr-1.5" /> Block Item
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-border/20 bg-muted/10 hover:bg-transparent">
                  <TableHead className="pl-6 font-mono text-[9px] uppercase font-black tracking-wider">Type</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black tracking-wider">Value</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black tracking-wider">Reason</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black tracking-wider">Source</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black tracking-wider">Expires</TableHead>
                  <TableHead className="pr-6 text-right font-mono text-[9px] uppercase font-black tracking-wider">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {blockedItems.length === 0 ? (
                  <TableRow><TableCell colSpan={6} className="text-center py-8 text-muted-foreground font-mono text-xs">No active blocks.</TableCell></TableRow>
                ) : blockedItems.map((item) => (
                  <TableRow key={item.id} className="hover:bg-muted/10 border-border/10">
                    <TableCell className="pl-6">
                      <Badge variant="outline" className={`text-[9px] ${
                        item.type === "ip" ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                          : item.type === "hash" ? "bg-purple-500/10 text-purple-400 border-purple-500/30"
                          : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                      }`}>{item.type.toUpperCase()}</Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs font-bold text-foreground max-w-[200px] truncate">{item.value}</TableCell>
                    <TableCell className="text-[10px] text-muted-foreground font-mono">{item.reason}</TableCell>
                    <TableCell className="text-[10px] font-mono">
                      <span className={item.blocked_by === "playbook-ai" ? "text-primary font-bold" : "text-foreground"}>{item.blocked_by}</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <Clock className="h-3 w-3 text-muted-foreground/40" />
                        <span className={`text-[10px] font-mono font-bold ${daysUntilExpiry(item.expires_at) <= 1 ? "text-rose-400" : "text-muted-foreground"}`}>
                          {formatDate(item.expires_at)} ({daysUntilExpiry(item.expires_at)}d)
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="pr-6 text-right">
                      <Button variant="ghost" size="sm" onClick={() => setConfirmRelease(item)}
                        className="text-[9px] uppercase font-extrabold text-amber-400 hover:bg-amber-500/10 h-7 tracking-wider">
                        <ShieldOff className="h-3 w-3 mr-1" /> Release
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Dialogs */}
      <AddBlockModal open={showAddBlock} onClose={() => setShowAddBlock(false)} onAdd={addBlock} />
      <SimulationDialog open={showSimulation} onClose={() => setShowSimulation(false)} />
      <ConfirmActionDialog
        open={!!confirmRelease}
        onOpenChange={() => setConfirmRelease(null)}
        title="Release Block"
        description={`Remove block on ${confirmRelease?.type.toUpperCase()} ${confirmRelease?.value}?`}
        actionLabel="Release Block"
        actionVariant="warning"
        targetLabel={`${confirmRelease?.type.toUpperCase()}: ${confirmRelease?.value ?? ""}`}
        requireReason requireTicketId
        onConfirm={releaseBlock}
      />
    </div>
  );
}
