import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Search, Globe, ShieldAlert, ExternalLink, Copy, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

interface IocResult {
  source: string;
  malicious: boolean;
  reputation: number;
  details: string;
}

interface IocLookupResponse {
  malicious: boolean;
  reputation: number;
  sources: string[];
  enrichment: {
    virus_total?: { score: number; malicious: number; suspicious: number };
    abuse_ipdb?: { score: number; total_reports: number };
    misp?: { count: number; matches: string[] };
    urlhaus?: { matched: boolean; threat?: string };
    alienvault_otx?: { matched: boolean; pulse_count: number; pulse_names?: string[] };
  };
}

interface IocSearchDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  ioc: string;
  iocType: "ip" | "domain" | "hash" | "url";
}

const API_BASE = "http://0.0.0.0:8000/api/v1";

export function IocSearchDialog({ open, onOpenChange, ioc, iocType }: IocSearchDialogProps) {
  const [results, setResults] = useState<IocResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !ioc) return;
    setLoading(true);
    setError(null);
    setResults([]);

    fetch(`${API_BASE}/threat-intel/lookup-ioc`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ioc, ioc_type: iocType }),
    })
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: IocLookupResponse) => {
        const parsed: IocResult[] = [];
        if (data.enrichment?.virus_total) {
          parsed.push({
            source: "VirusTotal",
            malicious: data.enrichment.virus_total.malicious > 0,
            reputation: data.enrichment.virus_total.score,
            details: `${data.enrichment.virus_total.malicious} malicious, ${data.enrichment.virus_total.suspicious} suspicious`,
          });
        }
        if (data.enrichment?.abuse_ipdb) {
          parsed.push({
            source: "AbuseIPDB",
            malicious: data.enrichment.abuse_ipdb.score > 25,
            reputation: data.enrichment.abuse_ipdb.score,
            details: `${data.enrichment.abuse_ipdb.total_reports} reports`,
          });
        }
        if (data.enrichment?.misp) {
          parsed.push({
            source: "MISP",
            malicious: data.enrichment.misp.count > 0,
            reputation: data.enrichment.misp.count > 0 ? 0 : 100,
            details: `${data.enrichment.misp.count} matching events`,
          });
        }
        if (data.enrichment?.urlhaus) {
          parsed.push({
            source: "URLhaus",
            malicious: data.enrichment.urlhaus.matched,
            reputation: data.enrichment.urlhaus.matched ? 0 : 100,
            details: data.enrichment.urlhaus.threat || "No match",
          });
        }
        if (data.enrichment?.alienvault_otx) {
          parsed.push({
            source: "AlienVault OTX",
            malicious: data.enrichment.alienvault_otx.matched,
            reputation: data.enrichment.alienvault_otx.matched ? Math.max(0, 100 - data.enrichment.alienvault_otx.pulse_count * 10) : 100,
            details: data.enrichment.alienvault_otx.pulse_count
              ? `${data.enrichment.alienvault_otx.pulse_count} pulses${data.enrichment.alienvault_otx.pulse_names?.length ? `: ${data.enrichment.alienvault_otx.pulse_names?.slice(0, 2).join(", ")}` : ""}`
              : "No pulses",
          });
        }
        if (parsed.length === 0) {
          parsed.push({ source: "Lookup", malicious: data.malicious, reputation: data.reputation, details: `Overall: ${data.malicious ? "malicious" : "clean"} (reputation: ${data.reputation})` });
        }
        setResults(parsed);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || "Backend unavailable");
        setResults([]);
        setLoading(false);
      });
  }, [open, ioc, iocType]);

  const copyIoc = () => {
    navigator.clipboard.writeText(ioc);
    toast.success("IOC copied to clipboard");
  };

  const searchAllAlerts = () => {
    const searchUrl = `/soc/alert-forensics?q=${encodeURIComponent(ioc)}`;
    toast.success("Cross-referencing IOC across alerts...", { description: `Searching for ${ioc} in alert-forensics.` });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg border-border/40">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-1">
            <div className={`p-2 rounded-lg ${
              iocType === "ip" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                : iocType === "domain" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                : "bg-purple-500/10 text-purple-400 border border-purple-500/20"
            }`}>
              <Globe className="h-4 w-4" />
            </div>
            <div>
              <DialogTitle className="text-sm font-bold font-mono">{ioc}</DialogTitle>
              <DialogDescription className="text-[10px] uppercase tracking-wider font-bold">
                {iocType.toUpperCase()} Indicator — Threat Feed Correlation
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="flex gap-2 mb-2">
          <Button variant="outline" size="sm" onClick={copyIoc} className="text-[10px] font-bold h-7 gap-1.5">
            <Copy className="h-3 w-3" /> Copy
          </Button>
          <Button variant="outline" size="sm" onClick={searchAllAlerts} className="text-[10px] font-bold h-7 gap-1.5">
            <Search className="h-3 w-3" /> Search Events
          </Button>
          <Button variant="outline" size="sm" onClick={() => {
            const url = iocType === "ip" ? `https://www.virustotal.com/gui/ip-address/${ioc}`
              : iocType === "hash" ? `https://www.virustotal.com/gui/file/${ioc}`
              : iocType === "domain" ? `https://www.virustotal.com/gui/domain/${ioc}`
              : `https://www.virustotal.com/gui/search/${ioc}`;
            window.open(url, "_blank", "noopener,noreferrer");
          }} className="text-[10px] font-bold h-7 gap-1.5 ml-auto">
            <ExternalLink className="h-3 w-3" /> VT Report
          </Button>
        </div>

        {loading ? (
          <div className="space-y-3 py-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 rounded-xl bg-muted/10 animate-pulse border border-border/20" />
            ))}
          </div>
        ) : error ? (
          <Alert variant="destructive" className="border-rose-500/30">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle className="text-[10px] uppercase tracking-wider font-bold">Lookup Failed</AlertTitle>
            <AlertDescription className="text-[10px]">
              {error}. The backend threat intel service may be unavailable.
            </AlertDescription>
          </Alert>
        ) : results.length > 0 ? (
          <ScrollArea className="max-h-[300px]">
            <div className="space-y-2">
              {results.map((r, i) => (
                <div key={i} className={`p-3 rounded-xl border ${
                  r.malicious
                    ? "bg-rose-500/5 border-rose-500/20"
                    : "bg-emerald-500/5 border-emerald-500/20"
                }`}>
                  <div className="flex justify-between items-start mb-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className={`text-[9px] font-mono ${
                        r.malicious
                          ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                          : "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                      }`}>
                        {r.source}
                      </Badge>
                      {r.malicious && <ShieldAlert className="h-3 w-3 text-rose-400" />}
                    </div>
                    <span className={`text-[10px] font-mono font-bold ${r.malicious ? "text-rose-400" : "text-emerald-400"}`}>
                      {r.malicious ? `Malicious (${r.reputation}%)` : "Clean"}
                    </span>
                  </div>
                  <p className="text-[10px] text-muted-foreground/70 font-mono">{r.details}</p>
                </div>
              ))}
            </div>
          </ScrollArea>
        ) : (
          <div className="py-6 text-center text-muted-foreground/60 text-[11px] font-mono">
            No enrichment data returned for this IOC.
          </div>
        )}

        {!error && (
          <Alert className="bg-primary/5 border-primary/20">
            <ShieldAlert className="h-4 w-4 text-primary" />
            <AlertTitle className="text-[10px] uppercase tracking-wider font-bold text-primary">Cross-Reference</AlertTitle>
            <AlertDescription className="text-[10px] text-muted-foreground">
              Click "Search Events" to find all internal alerts matching this IOC.
            </AlertDescription>
          </Alert>
        )}
      </DialogContent>
    </Dialog>
  );
}
