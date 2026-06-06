import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Copy, Download } from "lucide-react";
import { toast } from "sonner";

interface AlertDetail {
  event_id: string;
  timestamp: string;
  severity: number;
  risk_score: number;
  mitre_tactic: string | null;
  mitre_technique: string | null;
  source_tool: string;
  attack_type: string;
  host: string;
  dst_host: string;
  user: string | null;
  status: string;
  analyst_verdict: string;
  asset_criticality: string;
  raw_data?: Record<string, unknown>;
  enrichment_data?: Record<string, unknown>;
  soc_reasoning?: Record<string, unknown>;
}

interface AlertDetailDrawerProps {
  alert: AlertDetail | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AlertDetailDrawer({ alert, open, onOpenChange }: AlertDetailDrawerProps) {
  if (!alert) return null;

  const copyRawData = () => {
    const payload = JSON.stringify({
      event_id: alert.event_id,
      timestamp: alert.timestamp,
      severity: alert.severity,
      risk_score: alert.risk_score,
      mitre_tactic: alert.mitre_tactic,
      mitre_technique: alert.mitre_technique,
      source_tool: alert.source_tool,
      attack_type: alert.attack_type,
      host: alert.host,
      dst_host: alert.dst_host,
      user: alert.user,
      status: alert.status,
      analyst_verdict: alert.analyst_verdict,
      asset_criticality: alert.asset_criticality,
      raw_data: alert.raw_data,
      enrichment_data: alert.enrichment_data,
      soc_reasoning: alert.soc_reasoning,
    }, null, 2);
    navigator.clipboard.writeText(payload);
    toast.success("Raw JSON copied to clipboard");
  };

  const downloadJson = () => {
    const payload = JSON.stringify(alert, null, 2);
    const blob = new Blob([payload], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${alert.event_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Alert JSON downloaded");
  };

  const getSeverityBadge = (sev: number) => {
    if (sev >= 12) return "bg-rose-500/15 text-rose-400 border-rose-500/30";
    if (sev >= 8) return "bg-orange-500/15 text-orange-400 border-orange-500/30";
    if (sev >= 4) return "bg-yellow-500/15 text-yellow-400 border-yellow-500/30";
    return "bg-blue-500/15 text-blue-400 border-blue-500/30";
  };

  const getVerdictBadge = (verdict: string) => {
    switch (verdict) {
      case "true_positive": return "bg-rose-500/15 text-rose-400 border-rose-500/30";
      case "false_positive": return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
      default: return "bg-muted/20 text-muted-foreground border-border/30";
    }
  };

  const sections = [
    { label: "Event Details", data: { "Event ID": alert.event_id, "Timestamp": alert.timestamp, "Severity": `Level ${alert.severity}`, "Risk Score": alert.risk_score, "Status": alert.status } },
    { label: "MITRE ATT&CK", data: { "Tactic": alert.mitre_tactic ?? "N/A", "Technique": alert.mitre_technique ?? "N/A" } },
    { label: "Host Context", data: { "Source Host": alert.host, "Target Host": alert.dst_host, "User": alert.user ?? "N/A", "Asset Criticality": alert.asset_criticality } },
    { label: "Detection", data: { "Attack Type": alert.attack_type, "Source Tool": alert.source_tool } },
    { label: "Analyst Verdict", data: { "Verdict": alert.analyst_verdict === "true_positive" ? "True Positive" : alert.analyst_verdict === "false_positive" ? "False Positive" : "Unassigned" } },
  ];

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-xl border-border/40 bg-background/95 backdrop-blur-xl">
        <SheetHeader className="border-b border-border/30 pb-4 mb-4">
          <div className="flex items-center justify-between">
            <SheetTitle className="text-base font-mono font-bold flex items-center gap-2">
              <span className="text-primary">#</span>
              {alert.event_id}
            </SheetTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className={getSeverityBadge(alert.severity)}>
                Level {alert.severity}
              </Badge>
              <Badge variant="outline" className={getVerdictBadge(alert.analyst_verdict)}>
                {alert.analyst_verdict === "true_positive" ? "TP" : alert.analyst_verdict === "false_positive" ? "FP" : "N/A"}
              </Badge>
            </div>
          </div>
        </SheetHeader>

        <div className="flex gap-2 mb-4">
          <Button variant="outline" size="sm" onClick={copyRawData} className="text-[10px] font-bold h-7 gap-1.5">
            <Copy className="h-3 w-3" /> Copy Raw JSON
          </Button>
          <Button variant="outline" size="sm" onClick={downloadJson} className="text-[10px] font-bold h-7 gap-1.5">
            <Download className="h-3 w-3" /> Export
          </Button>
        </div>

        <ScrollArea className="h-[calc(100vh-220px)]">
          <div className="space-y-4">
            {sections.map((section) => (
              <div key={section.label} className="rounded-xl border border-border/30 bg-muted/5 p-4">
                <p className="text-[9px] uppercase tracking-widest font-black text-muted-foreground/50 mb-3">
                  {section.label}
                </p>
                <div className="space-y-2">
                  {Object.entries(section.data).map(([key, value]) => (
                    <div key={key} className="flex justify-between items-start gap-4 text-xs">
                      <span className="text-muted-foreground/70 font-mono shrink-0">{key}</span>
                      <span className="text-foreground font-mono font-semibold text-right break-all max-w-[60%]">
                        {String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {/* Raw JSON */}
            <div className="rounded-xl border border-border/30 bg-muted/5 p-4">
              <p className="text-[9px] uppercase tracking-widest font-black text-muted-foreground/50 mb-3">
                Raw Payload
              </p>
              <pre className="text-[10px] font-mono text-muted-foreground bg-black/40 p-3 rounded-lg border border-border/20 overflow-x-auto max-h-[300px] whitespace-pre-wrap break-all">
                {JSON.stringify({
                  raw_data: alert.raw_data,
                  enrichment_data: alert.enrichment_data,
                  soc_reasoning: alert.soc_reasoning,
                }, null, 2)}
              </pre>
            </div>
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
