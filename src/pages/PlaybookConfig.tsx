import { useState, useMemo, useCallback } from "react";
import { useDashboardData } from "@/hooks/useDashboardData";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Workflow, Plus, Play, Pause, Edit, Trash2, GitBranch,
  ToggleLeft, ToggleRight,
  RefreshCw, Save, RotateCcw, Terminal,
} from "lucide-react";
import { toast } from "sonner";
import type { PlaybookRule } from "@/types/playbook";
import AddRuleModal from "@/components/playbook/AddRuleModal";

const API_BASE = "http://0.0.0.0:8000/api/v1";

interface PlaybookData {
  page: string;
  playbook_library: { rules: PlaybookRule[]; default_action: string; total_rules: number };
  execution_history: { outcomes: Record<string, number>; total_executions: number };
}

const FALLBACK: PlaybookData = {
  page: "Playbook Config",
  playbook_library: { rules: [], default_action: "log_event", total_rules: 0 },
  execution_history: { outcomes: {}, total_executions: 0 },
};

/* ─── Rule Edit Modal (unique to admin config) ─────────────────────────── */

function RuleEditModal({ rule, onClose, onSave }: { rule: PlaybookRule | null; onClose: () => void; onSave: (r: PlaybookRule) => void }) {
  const [name, setName] = useState(rule?.name ?? "");
  const [action, setAction] = useState(rule?.action ?? "block_ip");
  const [confidence, setConfidence] = useState(String((rule?.confidence ?? 0.85) * 100));
  const [automation, setAutomation] = useState(rule?.automation_level ?? "semi");
  const [reason, setReason] = useState(rule?.reason ?? "");
  const [minRisk, setMinRisk] = useState(String(rule?.conditions?.min_risk_score ?? "40"));
  const [minSev, setMinSev] = useState(String(rule?.conditions?.min_severity ?? "5"));
  const [tags, setTags] = useState((rule?.conditions?.tags_contain ?? []).join(", "));

  if (!rule) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-[hsl(var(--background))] border border-border/40 rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="px-6 py-4 border-b border-border/30">
          <h3 className="text-lg font-bold">Edit Rule: {rule.name.replace(/_/g, " ")}</h3>
          <p className="text-xs text-muted-foreground/60">Modify playbook rule configuration</p>
        </div>
        <div className="px-6 py-4 space-y-4 max-h-[60vh] overflow-y-auto">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Rule Name</label>
              <Input value={name} onChange={e => setName(e.target.value)} className="bg-background/50 border-border/30 text-xs font-mono" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Action</label>
              <select value={action} onChange={e => setAction(e.target.value)}
                className="w-full bg-background/50 border border-border/30 text-xs px-3 py-2 rounded-lg text-foreground focus:ring-1 focus:ring-primary outline-none">
                {["isolate_host", "block_ip", "full_remediation", "password_reset", "create_case", "session_terminate", "log_event"].map(a => (
                  <option key={a} value={a}>{a.replace(/_/g, " ").toUpperCase()}</option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Confidence (%)</label>
              <Input value={confidence} onChange={e => setConfidence(e.target.value)} className="bg-background/50 border-border/30 text-xs font-mono" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Automation</label>
              <select value={automation} onChange={e => setAutomation(e.target.value)}
                className="w-full bg-background/50 border border-border/30 text-xs px-3 py-2 rounded-lg text-foreground focus:ring-1 focus:ring-primary outline-none">
                <option value="full">FULL</option><option value="semi">SEMI</option><option value="manual">MANUAL</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Min Risk Score</label>
              <Input value={minRisk} onChange={e => setMinRisk(e.target.value)} className="bg-background/50 border-border/30 text-xs font-mono" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Min Severity</label>
              <Input value={minSev} onChange={e => setMinSev(e.target.value)} className="bg-background/50 border-border/30 text-xs font-mono" />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Required Tags</label>
            <Input value={tags} onChange={e => setTags(e.target.value)} placeholder="malware, c2" className="bg-background/50 border-border/30 text-xs font-mono" />
          </div>
          <div className="space-y-2">
            <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Reason</label>
            <Input value={reason} onChange={e => setReason(e.target.value)} className="bg-background/50 border-border/30 text-xs" />
          </div>
        </div>
        <div className="px-6 py-4 border-t border-border/30 flex justify-end gap-3">
          <Button variant="outline" size="sm" onClick={onClose}>Cancel</Button>
          <Button size="sm" onClick={() => {
            onSave({
              ...rule,
              name, action, reason,
              confidence: (parseFloat(confidence) || 85) / 100,
              automation_level: automation,
              conditions: {
                min_risk_score: parseInt(minRisk) || 0,
                min_severity: parseInt(minSev) || 0,
                ...(tags.trim() ? { tags_contain: tags.split(",").map(t => t.trim()).filter(Boolean) } : {}),
              },
            });
            onClose();
          }}>
            <Save className="h-3.5 w-3.5 mr-1.5" /> Save Changes
          </Button>
        </div>
      </div>
    </div>
  );
}

/* ─── Main Page ─────────────────────────────────────────────────────────── */

export default function PlaybookConfig() {
  const { data, loading, refetch } = useDashboardData<PlaybookData>("playbooks-automation.json", FALLBACK);

  const [rules, setRules] = useState<PlaybookRule[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [editingRule, setEditingRule] = useState<PlaybookRule | null>(null);

  useMemo(() => {
    if (data?.playbook_library?.rules) setRules(data.playbook_library.rules);
  }, [data]);

  const history = data?.execution_history ?? FALLBACK.execution_history;

  const syncBackend = useCallback((method: string, path: string, body?: any) => {
    fetch(`${API_BASE}${path}`, {
      method, headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    }).catch(() => {});
  }, []);

  const addRule = useCallback((rule: PlaybookRule) => {
    setRules(prev => [...prev, rule]);
    syncBackend("POST", "/playbook-config/rules", {
      name: rule.name, action: rule.action, confidence: rule.confidence,
      automation_level: rule.automation_level, reason: rule.reason,
      conditions: rule.conditions,
    });
    toast.success("Rule Created", { description: `${rule.name} added to playbook library.` });
  }, [syncBackend]);

  const saveRule = useCallback((rule: PlaybookRule) => {
    setRules(prev => prev.map(r => r.name === rule.name ? rule : r));
    syncBackend("PUT", "/playbook-config/", {
      rules: rules.map(r => r.name === rule.name ? rule : r),
      default_action: "log_event",
    });
    toast.success("Rule Updated", { description: `${rule.name} configuration saved.` });
  }, [rules, syncBackend]);

  const toggleRule = useCallback((name: string) => {
    setRules(prev => {
      const updated = prev.map(r => r.name === name ? { ...r, enabled: !r.enabled } : r);
      const rule = prev.find(r => r.name === name);
      toast.success(rule?.enabled ? "Rule Disabled" : "Rule Enabled", { description: `${name} ${rule?.enabled ? "disabled" : "enabled"}` });
      syncBackend("PUT", "/playbook-config/", { rules: updated, default_action: "log_event" });
      return updated;
    });
  }, [syncBackend]);

  const deleteRule = useCallback((name: string) => {
    setRules(prev => prev.filter(r => r.name !== name));
    syncBackend("DELETE", `/playbook-config/rules/${encodeURIComponent(name)}`);
    toast.success("Rule Deleted", { description: `${name} removed from library.` });
  }, [syncBackend]);

  const resetDefaults = useCallback(() => {
    const defaults: PlaybookRule[] = [
      { name: "critical_threat", enabled: true, conditions: { tags_contain: ["C2", "misp_hit"], min_risk_score: 80, min_severity: 12 }, action: "isolate_host", confidence: 0.98, automation_level: "full", reason: "Critical threat: Automated host isolation.", triggers: 0 },
      { name: "high_risk_activity", enabled: true, conditions: { tags_contain: ["malware", "brute_force"], min_risk_score: 60, min_severity: 8 }, action: "block_ip", confidence: 0.85, automation_level: "full", reason: "High risk: Automated IP block.", triggers: 0 },
      { name: "low_risk_log", enabled: true, conditions: {}, action: "log_event", confidence: 0.5, automation_level: "manual", reason: "Low risk: Logged for reference.", triggers: 0 },
    ];
    setRules(defaults);
    syncBackend("POST", "/playbook-config/reset");
    toast.success("Defaults Restored");
  }, [syncBackend]);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-10 w-64 bg-muted/40 rounded-lg" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-24 bg-card/30 border border-border/20 rounded-xl" />)}
        </div>
        <div className="h-64 bg-card/30 border border-border/20 rounded-xl" />
      </div>
    );
  }

  const activeCount = rules.filter(r => r.enabled).length;
  const totalExec = history.total_executions ?? 0;

  return (
    <div className="w-full space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground flex items-center gap-3">
            <Workflow className="h-7 w-7 text-primary" />
            Playbook Configuration
          </h1>
          <p className="text-muted-foreground text-sm">Manage automated response rules and playbook engine settings</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={resetDefaults} className="text-xs gap-1.5">
            <RotateCcw className="h-3.5 w-3.5" /> Reset Defaults
          </Button>
          <Button variant="outline" size="sm" onClick={refetch} className="text-xs gap-1.5">
            <RefreshCw className="h-3.5 w-3.5" /> Sync
          </Button>
          <Button size="sm" onClick={() => setShowAdd(true)}>
            <Plus className="h-4 w-4 mr-1.5" /> New Rule
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: "Total Rules", value: rules.length, icon: <Workflow className="h-4 w-4" />, color: "text-primary", bg: "bg-primary/10 border-primary/20" },
          { label: "Active Rules", value: activeCount, icon: <Play className="h-4 w-4" />, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
          { label: "Paused Rules", value: rules.length - activeCount, icon: <Pause className="h-4 w-4" />, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
          { label: "Total Executions", value: totalExec.toLocaleString(), icon: <GitBranch className="h-4 w-4" />, color: "text-violet-400", bg: "bg-violet-500/10 border-violet-500/20" },
        ].map((s) => (
          <Card key={s.label} className="bg-card/20 border-border/40 backdrop-blur-md">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-xs font-bold text-muted-foreground/60 uppercase tracking-widest">{s.label}</CardTitle>
              <div className={`p-2 rounded-lg ${s.bg} ${s.color}`}>{s.icon}</div>
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-black font-mono ${s.color}`}>{s.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Rule Engine Table (admin config — detailed editing) */}
      <Card className="glass border-border/40 shadow-xl backdrop-blur-md overflow-hidden">
        <CardHeader className="border-b border-border/40 pb-4">
          <CardTitle className="text-lg font-bold flex items-center gap-2">
            <Terminal className="h-4 w-4 text-primary" />
            Rule Engine
          </CardTitle>
          <CardDescription>Configure trigger conditions, response actions, confidence thresholds, and automation levels</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto max-h-[500px] overflow-y-auto custom-scrollbar">
            <Table>
              <TableHeader>
                <TableRow className="border-border/20 bg-muted/10 hover:bg-transparent">
                  <TableHead className="pl-4 w-8" />
                  <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Rule</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Action</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Conditions</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Confidence</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Mode</TableHead>
                  <TableHead className="font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Triggers</TableHead>
                  <TableHead className="pr-4 font-mono text-[9px] uppercase font-black text-muted-foreground/50 tracking-wider">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rules.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-12 text-muted-foreground/50 font-mono text-xs">
                      No rules configured. Click "New Rule" to create one.
                    </TableCell>
                  </TableRow>
                ) : rules.map((rule) => (
                  <TableRow key={rule.name} className={`hover:bg-muted/10 border-border/10 ${!rule.enabled ? "opacity-50" : ""}`}>
                    <TableCell className="pl-4">
                      <button onClick={() => toggleRule(rule.name)} className="hover:scale-110 transition-transform">
                        {rule.enabled
                          ? <ToggleRight className="h-4 w-4 text-emerald-400" />
                          : <ToggleLeft className="h-4 w-4 text-muted-foreground/40" />}
                      </button>
                    </TableCell>
                    <TableCell>
                      <span className="font-mono text-xs font-bold text-foreground/80">{rule.name.replace(/_/g, " ")}</span>
                      <p className="text-[9px] text-muted-foreground/40 font-mono truncate max-w-[200px]">{rule.reason}</p>
                    </TableCell>
                    <TableCell>
                      <Badge className={
                        ["isolate_host", "full_remediation"].includes(rule.action)
                          ? "bg-rose-500/15 text-rose-400 border-rose-500/30 text-[9px]"
                          : rule.action === "block_ip"
                          ? "bg-orange-500/15 text-orange-400 border-orange-500/30 text-[9px]"
                          : ["password_reset", "session_terminate"].includes(rule.action)
                          ? "bg-amber-500/15 text-amber-400 border-amber-500/30 text-[9px]"
                          : "bg-primary/10 text-primary border-primary/20 text-[9px]"
                      }>
                        {rule.action.replace(/_/g, " ").toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-[9px] font-mono text-muted-foreground/60 max-w-[140px]">
                      {rule.conditions?.min_risk_score ? `Risk≥${rule.conditions.min_risk_score}` : ""}
                      {rule.conditions?.min_severity ? ` Sev≥${rule.conditions.min_severity}` : ""}
                      {rule.conditions?.tags_contain?.length ? ` [${rule.conditions.tags_contain.join(",")}]` : ""}
                      {!Object.keys(rule.conditions || {}).length ? "—" : ""}
                    </TableCell>
                    <TableCell>
                      <span className="font-mono text-xs font-bold text-emerald-400">{(rule.confidence * 100).toFixed(0)}%</span>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={
                        rule.automation_level === "full" ? "text-emerald-400 border-emerald-500/20 text-[9px]"
                          : rule.automation_level === "semi" ? "text-amber-400 border-amber-500/20 text-[9px]"
                          : "text-primary border-primary/20 text-[9px]"
                      }>
                        {rule.automation_level.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs font-bold text-muted-foreground">{rule.triggers?.toLocaleString() || 0}</TableCell>
                    <TableCell className="pr-4">
                      <div className="flex gap-1">
                        <Button variant="ghost" size="sm" onClick={() => setEditingRule(rule)}
                          className="h-7 w-7 p-0 text-primary hover:text-primary" title="Edit rule">
                          <Edit className="h-3 w-3" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => deleteRule(rule.name)}
                          className="h-7 w-7 p-0 text-rose-400 hover:text-rose-300" title="Delete rule">
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Info */}
      <Card className="bg-primary/5 border-primary/20">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Workflow className="h-5 w-5 text-primary mt-0.5 shrink-0" />
            <div>
              <h4 className="font-bold text-foreground text-sm mb-1">Playbook Engine</h4>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Rules are evaluated in order. The first matching rule determines the response action.
                Automation levels: <span className="text-emerald-400 font-mono">FULL</span> (no human needed),
                <span className="text-amber-400 font-mono"> SEMI</span> (analyst confirms),
                <span className="text-primary font-mono"> MANUAL</span> (analyst executes).
                Disabled rules are skipped during evaluation.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Dialogs */}
      <AddRuleModal open={showAdd} onClose={() => setShowAdd(false)} onAdd={addRule} />
      <RuleEditModal rule={editingRule} onClose={() => setEditingRule(null)} onSave={saveRule} />
    </div>
  );
}
