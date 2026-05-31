import { useState, useEffect, useCallback, useRef } from "react";
import { jsPDF } from "jspdf";
import html2canvas from "html2canvas";
import { PageHeader } from "@/components/PageHeader";
import { CyberCard } from "@/components/CyberCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { 
  RefreshCw, 
  Activity, 
  FileSpreadsheet, 
  Download, 
  TrendingUp,
  Award,
  BookOpen,
  MessageSquare,
  Pin,
  Send
} from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";
import { toast } from "sonner";

const API_BASE = "http://0.0.0.0:8000/api/v1";

interface ReportingAuditData {
  page: string;
  shift_handover: {
    open_incidents: number;
    pending_escalations: number;
    total_events_in_scope: number;
    analyst_activity: Record<string, number>;
  };
  executive_reports: {
    mttr_trend: string;
    incident_trend: Record<string, number>;
    total_incidents: number;
    critical_incidents: number;
  };
  technical_reports: {
    total_iocs: number;
    attack_chains: number;
    affected_systems: number;
  };
  export_options: string[];
}

const fallbackDefault: ReportingAuditData = {
  page: "Reporting & Audit",
  shift_handover: {
    open_incidents: 0,
    pending_escalations: 0,
    total_events_in_scope: 0,
    analyst_activity: {}
  },
  executive_reports: {
    mttr_trend: "N/A (live data)",
    incident_trend: {},
    total_incidents: 0,
    critical_incidents: 0
  },
  technical_reports: {
    total_iocs: 0,
    attack_chains: 0,
    affected_systems: 0
  },
  export_options: []
};

interface HandoverNote {
  id: number;
  author: string;
  content: string;
  pinned: boolean;
  timestamp: Date;
}

export default function ReportingAuditPage() {
  const [data, setData] = useState<ReportingAuditData>(fallbackDefault);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fullDashboard, setFullDashboard] = useState<Record<string, any>>({});

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [repRes, dashRes] = await Promise.all([
        fetch(`${API_BASE}/ui/reporting-audit`),
        fetch(`${API_BASE}/ui/dashboard`).catch(() => null),
      ]);
      if (!repRes.ok) throw new Error(`Server returned ${repRes.status}`);
      const repJson = await repRes.json();
      setData({ ...fallbackDefault, ...repJson });
      if (dashRes?.ok) setFullDashboard(await dashRes.json());
    } catch (err: any) {
      console.error("Failed to fetch reporting audit data:", err);
      setError(err.message || "Failed to load reporting data.");
      toast.error("Telemetry Unavailable", {
        description: "Could not reach backend. Using fallback data.",
      });
      setData(fallbackDefault);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const [handoverNotes, setHandoverNotes] = useState<HandoverNote[]>([
    { id: 1, author: "asmith", content: "Ongoing malware investigation on host web-01 — EDR isolation active, awaiting Tier 3 review.", pinned: true, timestamp: new Date() },
    { id: 2, author: "lchen", content: "Phishing campaign targeting finance — 12 emails quarantined, 2 users clicked. Password resets completed.", pinned: false, timestamp: new Date() },
  ]);
  const [newNote, setNewNote] = useState("");
  const [shiftLeadName, setShiftLeadName] = useState("");
  const reportRef = useRef<HTMLDivElement>(null);

  const addHandoverNote = () => {
    if (!newNote.trim()) return;
    setHandoverNotes(prev => [{
      id: Date.now(),
      author: shiftLeadName || "current_analyst",
      content: newNote.trim(),
      pinned: false,
      timestamp: new Date(),
    }, ...prev]);
    setNewNote("");
    toast.success("Handover note added");
  };

  const togglePin = (id: number) => {
    setHandoverNotes(prev => prev.map(n => n.id === id ? { ...n, pinned: !n.pinned } : n));
  };

  const shift = data.shift_handover;
  const exec = data.executive_reports;
  const tech = data.technical_reports;

  // Per-analyst escalation counts from risk queue
  const analystEscalations: Record<string, number> = {};
  for (const ev of (fullDashboard.command_center?.risk_queue ?? [])) {
    const aa = ev.analyst_assigned;
    if (aa && ev.escalation_level && ev.escalation_level !== "none") {
      analystEscalations[aa] = (analystEscalations[aa] || 0) + 1;
    }
  }

  // Format Recharts analyst activity bar chart data with rich metrics
  const analystActivity = shift.analyst_activity && Object.keys(shift.analyst_activity).length > 0
    ? shift.analyst_activity
    : { asmith: 127, lchen: 98, mwilson: 74, ablack: 52, tpark: 41 };
  const totalAnalystIncidents = Object.values(analystActivity).reduce((s, v) => s + v, 0);
  const analystChartData = Object.entries(analystActivity).map(([key, val]) => ({
    name: key.toUpperCase(),
    incidents: val,
    pct: totalAnalystIncidents ? ((val / totalAnalystIncidents) * 100).toFixed(1) : "0",
    escalations: analystEscalations[key] ?? 0,
  })).sort((a, b) => b.incidents - a.incidents);

  // Format Recharts executive incident trend bar chart
  const trendChartData = Object.entries(exec.incident_trend || {}).map(([key, val]) => ({
    name: key,
    count: val
  }));

  const COLORS = [
    "hsl(var(--cyber-blue))",
    "hsl(var(--critical))",
    "hsl(var(--warning))",
    "hsl(var(--primary))",
    "hsl(var(--secondary))",
    "hsl(var(--info))",
    "hsl(var(--success))",
    "hsl(var(--accent))",
  ];

  const handleExport = async (format: string) => {
    const full = fullDashboard;

    const cmd = full.command_center || {};
    const ir = full.incident_response || {};
    const ti = full.threat_intel || {};
    const ai = full.ai_operations || {};
    const hygiene = full.it_hygiene || {};
    const pb = full.playbooks_automation || {};
    const assets = full.asset_intelligence || {};
    const health = full.admin_health || {};
    const rep = full.reporting_audit || data;

    const exportData = {
      report_metadata: {
        generated_at: new Date().toISOString(),
        period_covered: "Pipeline dataset (259K+ events)",
        data_sources: ["Wazuh (OpenSearch)", "NDJSON Pipeline", "TheHive", "Threat Feeds (VT, AbuseIPDB, MISP, OTX, URLhaus)"],
      },
      command_center: {
        total_events: cmd.top_metrics?.total_events ?? data.shift_handover.total_events_in_scope,
        critical_alerts: cmd.top_metrics?.critical_alerts ?? 0,
        high_alerts: cmd.top_metrics?.high_alerts ?? 0,
        active_campaigns: cmd.top_metrics?.active_campaigns ?? 0,
        suppression_rate: cmd.top_metrics?.suppression_rate ?? 0,
        noise_rate: cmd.top_metrics?.noise_rate ?? 0,
        false_positive_rate: cmd.top_metrics?.false_positive_rate ?? 0,
        true_positive_rate: cmd.top_metrics?.true_positive_rate ?? 0,
        severity_distribution: cmd.severity_distribution ?? {},
        attack_type_distribution: cmd.attack_type_distribution ?? {},
        mitre_tactics: cmd.mitre_heatmap ?? {},
        escalation_levels: cmd.escalation_levels ?? {},
        top_risk_events: (cmd.risk_queue ?? []).slice(0, 20),
      },
      analyst_workload: {
        shift_open_incidents: rep.shift_handover?.open_incidents ?? data.shift_handover.open_incidents,
        pending_escalations: rep.shift_handover?.pending_escalations ?? data.shift_handover.pending_escalations,
        analyst_activity: rep.shift_handover?.analyst_activity ?? data.shift_handover.analyst_activity,
        analyst_verdicts: cmd.noise_reduction?.analyst_verdicts ?? {},
        per_analyst_detail: Object.entries(rep.shift_handover?.analyst_activity ?? data.shift_handover.analyst_activity).map(([name, total]) => {
          const escs = (cmd.risk_queue ?? []).filter((e: any) => e.analyst_assigned === name && e.escalation_level && e.escalation_level !== "none").length;
          return { name, total_incidents: total, escalations: escs };
        }).sort((a: any, b: any) => b.total_incidents - a.total_incidents),
      },
      ai_operations: {
        model_f1_score: ai.model_health?.f1_score ?? 0,
        model_precision: ai.model_health?.precision ?? 0,
        model_recall: ai.model_health?.recall ?? 0,
        total_classified: ai.model_health?.total_classified ?? 0,
        avg_confidence: ai.model_health?.avg_confidence ?? 0,
        auto_closed_alerts: ai.ai_decision_queue?.auto_closed_alerts ?? 0,
        suppressed_alerts: ai.ai_decision_queue?.suppressed_alerts ?? 0,
        escalated_alerts: ai.ai_decision_queue?.escalated_alerts ?? 0,
        low_confidence: ai.ai_decision_queue?.low_confidence_detections ?? 0,
        false_positives: ai.analyst_feedback?.false_positives ?? 0,
        true_positives: ai.analyst_feedback?.true_positives ?? 0,
        false_negatives: ai.analyst_feedback?.false_negatives ?? 0,
      },
      it_hygiene: {
        overall_score: hygiene.overall_hygiene_score ?? hygiene.hygiene_score?.overall ?? 0,
        patching: hygiene.hygiene_breakdown?.patching ?? hygiene.breakdown?.patching ?? 0,
        authentication: hygiene.hygiene_breakdown?.authentication ?? hygiene.breakdown?.authentication ?? 0,
        logging: hygiene.hygiene_breakdown?.logging ?? hygiene.breakdown?.logging ?? 0,
        integrity: hygiene.hygiene_breakdown?.integrity ?? hygiene.breakdown?.integrity ?? 0,
        threat_exposure: hygiene.hygiene_breakdown?.threat_exposure ?? hygiene.breakdown?.threat_exposure ?? 0,
        nist_coverage: hygiene.compliance?.nist ?? hygiene.nist_coverage ?? 0,
        cis_coverage: hygiene.compliance?.cis ?? hygiene.cis_coverage ?? 0,
        mitre_coverage: hygiene.compliance?.mitre ?? hygiene.mitre_coverage ?? 0,
        total_vulnerabilities: hygiene.total_vulnerabilities ?? 0,
        hosts_with_vulns: hygiene.hosts_with_vulnerabilities ?? 0,
      },
      threat_intelligence: {
        unique_ip_iocs: ti.ioc_intelligence?.unique_ips ?? ti.unique_ips ?? 0,
        unique_domain_iocs: ti.ioc_intelligence?.unique_domains ?? ti.unique_domains ?? 0,
        unique_hash_iocs: ti.ioc_intelligence?.unique_hashes ?? ti.unique_hashes ?? 0,
        unique_url_iocs: ti.ioc_intelligence?.unique_urls ?? ti.unique_urls ?? 0,
        total_campaigns: ti.campaign_intelligence?.total_campaigns ?? ti.total_campaigns ?? 0,
        top_campaigns: (ti.campaign_intelligence?.top_campaigns ?? ti.top_campaigns ?? []).slice(0, 10),
      },
      incident_response: {
        total_thehive_cases: ir.stats?.total_cases ?? 0,
        critical_cases: ir.stats?.critical_cases ?? 0,
        cases_by_severity: ir.stats?.cases_by_severity ?? {},
        top_tags: ir.stats?.top_tags ?? {},
        escalated_incidents: ir.stats?.escalated_incidents ?? 0,
        response_actions: ir.response_actions_available ?? [],
      },
      playbooks_automation: {
        total_rules: pb.total_rules ?? pb.rules?.length ?? 0,
        execution_history: pb.execution_history ?? {},
        simulation_enabled: pb.simulation_mode ?? false,
        approval_workflows: pb.approval_workflows ?? {},
      },
      asset_intelligence: {
        total_hosts_monitored: assets.total_hosts ?? assets.asset_count ?? 0,
        total_alerts: assets.total_alerts ?? 0,
        top_affected_hosts: (assets.top_hosts ?? []).slice(0, 10),
      },
      admin_health: {
        wazuh_status: health.connector_health?.wazuh_connector?.status ?? "unknown",
        misp_status: health.connector_health?.misp_connector?.status ?? "unknown",
        thehive_status: health.connector_health?.thehive_connector?.status ?? "unknown",
        threat_feeds: health.connector_health?.threat_feed_connectors ?? {},
        total_thehive_cases: health.connector_health?.thehive_connector?.cases ?? 0,
      },
      executive_reports: {
        total_incidents: rep.executive_reports?.total_incidents ?? data.executive_reports.total_incidents,
        critical_incidents: rep.executive_reports?.critical_incidents ?? data.executive_reports.critical_incidents,
        mttr_trend: rep.executive_reports?.mttr_trend ?? data.executive_reports.mttr_trend,
        incident_trend_monthly: rep.executive_reports?.incident_trend ?? data.executive_reports.incident_trend,
        iocs_found: rep.technical_reports?.total_iocs ?? data.technical_reports.total_iocs,
        attack_chains: rep.technical_reports?.attack_chains ?? data.technical_reports.attack_chains,
        affected_systems: rep.technical_reports?.affected_systems ?? data.technical_reports.affected_systems,
      },
      handover_notes: handoverNotes.map(n => ({ ...n, timestamp: n.timestamp.toISOString() })),
    };

    try {
      // NDJSON: download real SOC dataset from backend
      if (format === "ndjson") {
        const res = await fetch(`${API_BASE}/data-outputs/ndjson/latest`);
        if (!res.ok) throw new Error(`Backend returned ${res.status}`);
        const blob = await res.blob();
        const disposition = res.headers.get("content-disposition");
        const match = disposition?.match(/filename="?(.+?)"?$/);
        const filename = match?.[1] || `soc-dataset-${new Date().toISOString().slice(0, 10)}.ndjson`;
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a"); a.href = url; a.download = filename;
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success("NDJSON Export Complete", { description: `${filename} (${(blob.size / 1024 / 1024).toFixed(1)} MB)` });
        return;
      }

      // CSV: multi-section table-format SOC manager report
      if (format === "csv") {
        const esc = (v: any) => `"${String(v ?? "").replace(/"/g, '""')}"`;
        const rows: string[] = [];
        const tbl = (section: string, data: [string, string, any][]) => {
          data.forEach(([sub, metric, val]) => rows.push(`${esc(section)},${esc(sub)},${esc(metric)},${esc(val)}`));
        };

        rows.push("Section,Sub-Section,Metric,Value");

        tbl("Report Metadata", [
          ["", "Generated At", exportData.report_metadata.generated_at],
          ["", "Period Covered", exportData.report_metadata.period_covered],
          ["", "Data Sources", exportData.report_metadata.data_sources.join("; ")],
        ]);

        tbl("Command Center KPIs", [
          ["Volume", "Total Events", exportData.command_center.total_events],
          ["Volume", "Critical Alerts (Severity >= 10)", exportData.command_center.critical_alerts],
          ["Volume", "High Alerts (Severity 7-9)", exportData.command_center.high_alerts],
          ["Volume", "Active Campaigns", exportData.command_center.active_campaigns],
          ["Quality", "Suppression Rate (%)", exportData.command_center.suppression_rate],
          ["Quality", "Noise Rate (%)", exportData.command_center.noise_rate],
          ["Quality", "False Positive Rate (%)", exportData.command_center.false_positive_rate],
          ["Quality", "True Positive Rate (%)", exportData.command_center.true_positive_rate],
        ]);

        for (const [sev, cnt] of Object.entries(exportData.command_center.severity_distribution)) {
          tbl("Command Center KPIs", [["Severity Dist", `Severity ${sev}`, cnt]]);
        }
        for (const [atk, cnt] of Object.entries(exportData.command_center.attack_type_distribution).slice(0, 15)) {
          tbl("Command Center KPIs", [["Attack Type", atk, cnt]]);
        }
        for (const [tac, cnt] of Object.entries(exportData.command_center.mitre_tactics).slice(0, 15)) {
          tbl("Command Center KPIs", [["MITRE Tactic", tac, cnt]]);
        }

        tbl("Analyst Workload", [
          ["Shift", "Open Incidents", exportData.analyst_workload.shift_open_incidents],
          ["Shift", "Pending Escalations", exportData.analyst_workload.pending_escalations],
        ]);
        const aa = exportData.analyst_workload.analyst_activity || {};
        const totalAA = Object.values(aa).reduce((s: number, v: any) => s + Number(v), 0);
        for (const detail of exportData.analyst_workload.per_analyst_detail) {
          const pct = totalAA ? ((detail.total_incidents / totalAA) * 100).toFixed(1) : "0";
          tbl("Analyst Workload", [[`${detail.name} (Rank)`, "Total Incidents", detail.total_incidents]]);
          tbl("Analyst Workload", [[`${detail.name} (Rank)`, "Share of Total (%)", pct]]);
          tbl("Analyst Workload", [[`${detail.name} (Rank)`, "Escalations", detail.escalations]]);
        }

        tbl("AI Operations - Model Health", [
          ["Performance", "F1 Score", exportData.ai_operations.model_f1_score],
          ["Performance", "Precision", exportData.ai_operations.model_precision],
          ["Performance", "Recall", exportData.ai_operations.model_recall],
          ["Performance", "Total Classified", exportData.ai_operations.total_classified],
          ["Performance", "Average Confidence", exportData.ai_operations.avg_confidence],
        ]);

        tbl("AI Operations - Decision Queue", [
          ["Outcome", "Auto-Closed Alerts", exportData.ai_operations.auto_closed_alerts],
          ["Outcome", "Suppressed Alerts", exportData.ai_operations.suppressed_alerts],
          ["Outcome", "Escalated Alerts", exportData.ai_operations.escalated_alerts],
          ["Outcome", "Low Confidence Detections", exportData.ai_operations.low_confidence],
          ["Feedback", "False Positives", exportData.ai_operations.false_positives],
          ["Feedback", "True Positives", exportData.ai_operations.true_positives],
          ["Feedback", "False Negatives", exportData.ai_operations.false_negatives],
        ]);

        tbl("IT Hygiene & Compliance", [
          ["Score", "Overall Hygiene", exportData.it_hygiene.overall_score],
          ["Score", "Patching", exportData.it_hygiene.patching],
          ["Score", "Authentication", exportData.it_hygiene.authentication],
          ["Score", "Logging & Monitoring", exportData.it_hygiene.logging],
          ["Score", "Integrity", exportData.it_hygiene.integrity],
          ["Score", "Threat Exposure", exportData.it_hygiene.threat_exposure],
          ["Compliance", "NIST Framework Coverage (%)", exportData.it_hygiene.nist_coverage],
          ["Compliance", "CIS Controls Coverage (%)", exportData.it_hygiene.cis_coverage],
          ["Compliance", "MITRE ATT&CK Coverage (%)", exportData.it_hygiene.mitre_coverage],
          ["Vulnerabilities", "Total Vulnerabilities", exportData.it_hygiene.total_vulnerabilities],
          ["Vulnerabilities", "Hosts with Vulnerabilities", exportData.it_hygiene.hosts_with_vulns],
        ]);

        tbl("Threat Intelligence", [
          ["IOCs", "Unique IP IOCs", exportData.threat_intelligence.unique_ip_iocs],
          ["IOCs", "Unique Domain IOCs", exportData.threat_intelligence.unique_domain_iocs],
          ["IOCs", "Unique Hash IOCs", exportData.threat_intelligence.unique_hash_iocs],
          ["IOCs", "Unique URL IOCs", exportData.threat_intelligence.unique_url_iocs],
          ["Campaigns", "Total Campaigns", exportData.threat_intelligence.total_campaigns],
        ]);

        tbl("Incident Response", [
          ["Cases", "Total TheHive Cases", exportData.incident_response.total_thehive_cases],
          ["Cases", "Critical Cases", exportData.incident_response.critical_cases],
          ["Escalations", "Incidents Escalated", exportData.incident_response.escalated_incidents],
        ]);
        for (const [sev, cnt] of Object.entries(exportData.incident_response.cases_by_severity)) {
          tbl("Incident Response", [["Cases by Severity", sev, cnt]]);
        }
        for (const [tag, cnt] of Object.entries(exportData.incident_response.top_tags).slice(0, 10)) {
          tbl("Incident Response", [["Top Tags", tag, cnt]]);
        }

        tbl("Playbooks & Automation", [
          ["Rules", "Total Playbook Rules", exportData.playbooks_automation.total_rules],
          ["Mode", "Simulation Mode", exportData.playbooks_automation.simulation_enabled ? "Enabled" : "Disabled"],
        ]);

        tbl("Asset Intelligence", [
          ["Hosts", "Total Hosts Monitored", exportData.asset_intelligence.total_hosts_monitored],
          ["Alerts", "Total Alerts on Assets", exportData.asset_intelligence.total_alerts],
        ]);

        tbl("Admin - Connector Health", [
          ["Status", "Wazuh Connector", exportData.admin_health.wazuh_status],
          ["Status", "MISP Connector", exportData.admin_health.misp_status],
          ["Status", "TheHive Connector", exportData.admin_health.thehive_status],
          ["Cases", "TheHive Total Cases", exportData.admin_health.total_thehive_cases],
        ]);

        tbl("Executive Reports", [
          ["Volume", "Total Incidents", exportData.executive_reports.total_incidents],
          ["Volume", "Critical Incidents", exportData.executive_reports.critical_incidents],
          ["Trend", "MTTR Trend", exportData.executive_reports.mttr_trend],
          ["IOCs", "IOCs Found", exportData.executive_reports.iocs_found],
          ["Chains", "Attack Chains", exportData.executive_reports.attack_chains],
          ["Systems", "Affected Systems", exportData.executive_reports.affected_systems],
        ]);

        for (const note of exportData.handover_notes) {
          tbl("Handover Notes", [[note.author, note.pinned ? "PINNED" : "Note", note.content]]);
        }

        const blob = new Blob([rows.join("\n")], { type: "text/csv" });
        const filename = `soc-manager-report-${new Date().toISOString().slice(0, 10)}.csv`;
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a"); a.href = url; a.download = filename;
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success("SOC Manager Report Exported", { description: `${filename} (${(blob.size / 1024).toFixed(0)} KB)` });
        return;
      }

      // JSON: full structured export
      if (format === "json") {
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
        const filename = `soc-manager-report-${new Date().toISOString().slice(0, 10)}.json`;
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a"); a.href = url; a.download = filename;
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success("SOC Manager Report Exported", { description: `${filename} (${(blob.size / 1024).toFixed(0)} KB)` });
        return;
      }

      // PDF: visual report with html2canvas + jsPDF
      if (format === "pdf") {
        const el = reportRef.current;
        if (!el) { toast.error("PDF Export Failed", { description: "Report element not found" }); return; }
        toast.loading("Generating PDF...");
        const canvas = await html2canvas(el, {
          scale: 2,
          useCORS: true,
          logging: false,
          backgroundColor: "#0a0e1a",
        });
        const imgData = canvas.toDataURL("image/png");
        const pdf = new jsPDF("p", "mm", "a4");
        const pdfW = pdf.internal.pageSize.getWidth();
        const pdfH = (canvas.height * pdfW) / canvas.width;
        let heightLeft = pdfH;
        let position = 0;
        const pageH = pdf.internal.pageSize.getHeight() - 10;

        pdf.addImage(imgData, "PNG", 0, position, pdfW, pdfH);
        heightLeft -= pageH;
        while (heightLeft > 0) {
          position = heightLeft - pdfH;
          pdf.addPage();
          pdf.addImage(imgData, "PNG", 0, position, pdfW, pdfH);
          heightLeft -= pageH;
        }

        pdf.save(`soc-manager-report-${new Date().toISOString().slice(0, 10)}.pdf`);
        toast.dismiss();
        toast.success("SOC Manager Report Exported", { description: "PDF generated from live dashboard view." });
        return;
      }
    } catch (err) {
      toast.error("Export Failed", { description: String(err) });
    }
  };

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
    <div className="w-full h-full space-y-10 pb-16" ref={reportRef}>
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <PageHeader 
          title="Reporting & Shift Handover"
          description="Executive shift handover summaries, technical indicators audit logs, and PDF/CSV compliance generators"
          breadcrumbs={[{ label: "Admin" }, { label: "Reporting & Audit" }]}
        />
        <Button variant="outline" size="sm" onClick={fetchData} className="font-mono text-xs border-border/40 flex items-center gap-2 hover:bg-primary/5">
          <RefreshCw className="h-3.5 w-3.5" /> Force Audit Re-scan
        </Button>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <CyberCard delay={0.05} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <TrendingUp className="h-5 w-5" />
            </div>
            <Badge className="bg-primary/10 text-primary border border-primary/20 text-[10px]">SHIFT_TOTAL</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Shift Incidents Handled</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-foreground">{exec.total_incidents?.toLocaleString()}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.1} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500">
              <Activity className="h-5 w-5 animate-pulse" />
            </div>
            <Badge variant="outline" className="text-rose-500 bg-rose-500/5 border-rose-500/20 text-[10px]">SEV_4</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Critical Incident Volume</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-rose-500">{exec.critical_incidents?.toLocaleString()}</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.15} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <Award className="h-5 w-5" />
            </div>
            <Badge variant="outline" className="text-purple-400 bg-purple-500/5 border-purple-500/20 text-[10px]">CHAINS</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Attack Chains Analyzed</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-purple-400">{tech.attack_chains} Chains</h3>
          </div>
        </CyberCard>

        <CyberCard delay={0.2} className="bg-card/20 border-border/40">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-500">
              <BookOpen className="h-5 w-5" />
            </div>
            <Badge variant="outline" className="text-indigo-400 bg-indigo-500/5 border-indigo-500/20 text-[10px]">EXPORTS</Badge>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">Compliant Exports</p>
            <h3 className="text-3xl font-black font-mono tracking-tight text-indigo-400">3 Formats</h3>
          </div>
        </CyberCard>
      </div>

      {/* Main visual layouts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Analyst Activity Chart */}
        <Card className="lg:col-span-2 bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
          <CardHeader className="border-b border-border/40 pb-4">
            <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary animate-pulse" />
              Analyst Incident Resolution Volume
            </CardTitle>
            <CardDescription>Shift incident counts resolved by active security analysts</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            <div className="h-[240px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analystChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={8} tickLine={false} axisLine={false} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={9} tickLine={false} axisLine={false} />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      const d = payload[0].payload;
                      return (
                        <div className="bg-card/95 backdrop-blur-md border border-border/40 rounded-xl p-3 text-[11px] space-y-1.5 shadow-2xl">
                          <p className="font-bold text-foreground text-xs">{d.name}</p>
                          <div className="text-muted-foreground space-y-0.5">
                            <p>Incidents: <span className="text-foreground font-mono">{d.incidents}</span></p>
                            <p>Share: <span className="text-foreground font-mono">{d.pct}%</span></p>
                            <p>Escalations: <span className="text-foreground font-mono">{d.escalations}</span></p>
                          </div>
                          <div className="w-full bg-border/30 rounded-full h-1 mt-1">
                            <div className="bg-primary/70 h-1 rounded-full" style={{ width: `${Math.min(100, Number(d.pct))}%` }} />
                          </div>
                        </div>
                      );
                    }}
                  />
                  <Bar dataKey="incidents" radius={[4, 4, 0, 0]} barSize={20}>
                    {analystChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            {/* Analyst ranking summary table */}
            <div className="border border-border/20 rounded-xl overflow-hidden">
              <table className="w-full text-[10px] font-mono">
                <thead>
                  <tr className="bg-muted/10 border-b border-border/20">
                    <th className="text-left p-2 text-muted-foreground/60 font-black uppercase tracking-wider">Rank</th>
                    <th className="text-left p-2 text-muted-foreground/60 font-black uppercase tracking-wider">Analyst</th>
                    <th className="text-right p-2 text-muted-foreground/60 font-black uppercase tracking-wider">Incidents</th>
                    <th className="text-right p-2 text-muted-foreground/60 font-black uppercase tracking-wider">Share</th>
                    <th className="text-right p-2 text-muted-foreground/60 font-black uppercase tracking-wider">Escalations</th>
                  </tr>
                </thead>
                <tbody>
                  {analystChartData.map((a, i) => (
                    <tr key={a.name} className="border-b border-border/10 hover:bg-muted/5 transition-colors">
                      <td className="p-2 text-muted-foreground">#{i + 1}</td>
                      <td className="p-2 font-bold text-foreground">{a.name}</td>
                      <td className="p-2 text-right font-bold text-foreground">{a.incidents}</td>
                      <td className="p-2 text-right text-muted-foreground">{a.pct}%</td>
                      <td className="p-2 text-right">
                        <span className={`font-bold ${a.escalations > 0 ? "text-amber-400" : "text-muted-foreground"}`}>
                          {a.escalations}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Executive Handover stats & Export Deck */}
        <div className="space-y-6">
          
          {/* Export Deck */}
          <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
            <CardHeader className="border-b border-border/40 pb-4">
              <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
                <Download className="h-4 w-4 text-primary" />
                Audit Export Deck
              </CardTitle>
              <CardDescription>Generate compliance handover dossiers in multiple formats</CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-2.5">
              {(data.export_options?.length ? data.export_options : ["csv", "json", "ndjson", "pdf"]).map((opt, idx) => (
                <div key={idx} className="p-3.5 rounded-xl border border-border/30 bg-background/25 flex justify-between items-center group hover:border-border transition-all">
                  <div className="flex items-center gap-3">
                    <FileSpreadsheet className="h-4 w-4 text-primary group-hover:scale-110 transition-transform" />
                    <span className="font-mono text-xs font-bold text-foreground uppercase tracking-widest">{opt} Handover File</span>
                  </div>
                  <Button size="sm" variant="ghost" onClick={() => handleExport(opt)} className="text-[10px] uppercase font-bold text-primary hover:bg-primary/10 tracking-widest h-8">
                    Generate
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Collaborative Handover Panel */}
          <Card className="bg-card/25 border-border/40 shadow-xl backdrop-blur-md">
            <CardHeader className="border-b border-border/40 pb-4">
              <CardTitle className="text-lg font-bold font-grotesk flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-primary" />
                Collaborative Handover
              </CardTitle>
              <CardDescription>Shift lead notes, pinned incidents, and handover logs</CardDescription>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              {/* Stats summary */}
              <div className="grid grid-cols-3 gap-2 mb-2">
                <div className="bg-muted/10 rounded-lg p-2 text-center border border-border/20">
                  <p className="text-[8px] uppercase tracking-wider text-muted-foreground/50">Open</p>
                  <p className="text-lg font-black font-mono">{shift.open_incidents?.toLocaleString()}</p>
                </div>
                <div className="bg-muted/10 rounded-lg p-2 text-center border border-border/20">
                  <p className="text-[8px] uppercase tracking-wider text-muted-foreground/50">Pending</p>
                  <p className="text-lg font-black font-mono text-rose-400">{shift.pending_escalations?.toLocaleString()}</p>
                </div>
                <div className="bg-muted/10 rounded-lg p-2 text-center border border-border/20">
                  <p className="text-[8px] uppercase tracking-wider text-muted-foreground/50">In Scope</p>
                  <p className="text-lg font-black font-mono">{shift.total_events_in_scope?.toLocaleString()}</p>
                </div>
              </div>

              {/* Notes list */}
              <div className="space-y-1.5 max-h-[180px] overflow-y-auto custom-scrollbar">
                {handoverNotes.map(note => (
                  <div key={note.id} className={`p-2 rounded-lg border text-[10px] ${
                    note.pinned
                      ? "bg-primary/5 border-primary/20"
                      : "bg-muted/5 border-border/20"
                  }`}>
                    <div className="flex justify-between items-start mb-1">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono font-bold text-foreground">{note.author}</span>
                        {note.pinned && <Pin className="h-2.5 w-2.5 text-primary" />}
                      </div>
                      <Button variant="ghost" size="icon" className="h-4 w-4" onClick={() => togglePin(note.id)}>
                        <Pin className={`h-2.5 w-2.5 ${note.pinned ? "fill-primary text-primary" : "text-muted-foreground/40"}`} />
                      </Button>
                    </div>
                    <p className="text-muted-foreground/80 font-mono leading-relaxed">{note.content}</p>
                  </div>
                ))}
              </div>

              {/* Add note */}
              <div className="space-y-2 pt-2 border-t border-border/20">
                <div className="flex gap-2">
                  <Input
                    placeholder="Your name (optional)"
                    value={shiftLeadName}
                    onChange={(e) => setShiftLeadName(e.target.value)}
                    className="h-7 text-[10px] bg-background/50 border-border/40 w-28"
                  />
                  <Textarea
                    placeholder="Write handover note… describe ongoing incidents, critical tasks, or special instructions"
                    value={newNote}
                    onChange={(e) => setNewNote(e.target.value)}
                    className="min-h-[60px] text-[10px] bg-background/50 border-border/40 flex-1"
                  />
                </div>
                <Button size="sm" onClick={addHandoverNote} disabled={!newNote.trim()}
                  className="text-[10px] font-bold h-7 w-full gap-1.5">
                  <Send className="h-3 w-3" /> Post Handover Note
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
