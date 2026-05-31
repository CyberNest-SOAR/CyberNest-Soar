import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import type { PlaybookRule } from "@/types/playbook";

const ACTIONS = ["isolate_host", "block_ip", "full_remediation", "password_reset", "create_case", "session_terminate", "log_event"];

interface Props {
  open: boolean;
  onClose: () => void;
  onAdd: (rule: PlaybookRule) => void;
}

export default function AddRuleModal({ open, onClose, onAdd }: Props) {
  const [name, setName] = useState("");
  const [action, setAction] = useState("block_ip");
  const [confidence, setConfidence] = useState("85");
  const [automation, setAutomation] = useState("semi");
  const [reason, setReason] = useState("");
  const [minRisk, setMinRisk] = useState("40");
  const [minSev, setMinSev] = useState("5");
  const [tags, setTags] = useState("");

  if (!open) return null;

  const reset = () => {
    setName(""); setAction("block_ip"); setConfidence("85"); setAutomation("semi");
    setReason(""); setMinRisk("40"); setMinSev("5"); setTags("");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-[hsl(var(--background))] border border-border/40 rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="px-6 py-4 border-b border-border/30">
          <h3 className="text-lg font-bold">+ New Playbook Rule</h3>
          <p className="text-xs text-muted-foreground/60">Create a new automated response rule</p>
        </div>
        <div className="px-6 py-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Rule Name</label>
              <Input value={name} onChange={e => setName(e.target.value)} placeholder="my_rule" className="bg-background/50 border-border/30 text-xs font-mono" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Action</label>
              <select value={action} onChange={e => setAction(e.target.value)}
                className="w-full bg-background/50 border border-border/30 text-xs px-3 py-2 rounded-lg text-foreground focus:ring-1 focus:ring-primary outline-none">
                {ACTIONS.map(a => (
                  <option key={a} value={a}>{a.replace(/_/g, " ").toUpperCase()}</option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Confidence (%)</label>
              <Input value={confidence} onChange={e => setConfidence(e.target.value)} placeholder="85" className="bg-background/50 border-border/30 text-xs font-mono" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Automation</label>
              <select value={automation} onChange={e => setAutomation(e.target.value)}
                className="w-full bg-background/50 border border-border/30 text-xs px-3 py-2 rounded-lg text-foreground focus:ring-1 focus:ring-primary outline-none">
                <option value="full">FULL</option><option value="semi">SEMI</option><option value="manual">MANUAL</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Min Risk</label>
              <Input value={minRisk} onChange={e => setMinRisk(e.target.value)} placeholder="40" className="bg-background/50 border-border/30 text-xs font-mono" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Min Severity</label>
              <Input value={minSev} onChange={e => setMinSev(e.target.value)} placeholder="5" className="bg-background/50 border-border/30 text-xs font-mono" />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Required Tags (comma-separated)</label>
            <Input value={tags} onChange={e => setTags(e.target.value)} placeholder="malware, c2" className="bg-background/50 border-border/30 text-xs font-mono" />
          </div>
          <div className="space-y-2">
            <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/50">Reason</label>
            <Input value={reason} onChange={e => setReason(e.target.value)} placeholder="Automated response..." className="bg-background/50 border-border/30 text-xs" />
          </div>
        </div>
        <div className="px-6 py-4 border-t border-border/30 flex justify-end gap-3">
          <Button variant="outline" size="sm" onClick={() => { reset(); onClose(); }}>Cancel</Button>
          <Button size="sm" onClick={() => {
            if (!name) { toast.error("Rule name is required"); return; }
            onAdd({
              name, action, reason,
              confidence: (parseFloat(confidence) || 85) / 100,
              automation_level: automation,
              enabled: true, triggers: 0,
              conditions: {
                min_risk_score: parseInt(minRisk) || 0,
                min_severity: parseInt(minSev) || 0,
                ...(tags.trim() ? { tags_contain: tags.split(",").map(t => t.trim()).filter(Boolean) } : {}),
              },
            });
            reset();
            onClose();
          }} disabled={!name}>
            <Plus className="h-3.5 w-3.5 mr-1.5" /> Create Rule
          </Button>
        </div>
      </div>
    </div>
  );
}
