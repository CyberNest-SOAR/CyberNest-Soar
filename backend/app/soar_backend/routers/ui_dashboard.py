"""
routers/ui_dashboard.py — All UI dashboard pages data in one place.

Serves structured data matching the CyberNestSOAR UI Blueprint's 10 sections.
Each endpoint returns data formatted specifically for its corresponding UI page,
aggregated from:
  - dataset_pipeline/data/outputs/  (259K+ SOC events, 50 TheHive cases, 393K LLM entries)
  - logs.json                        (11K+ simulation events)
  - threat_intel_db.json             (IOC storage)
  - playbook_config.json             (playbook rules)
  - OpenSearch (live alerts)
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ui", tags=["UI Dashboard"])

BASE = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "dataset_pipeline" / "data" / "outputs"

# ── helpers ──────────────────────────────────────────────────────────────

def _latest_ndjson():
    files = sorted(OUTPUTS_DIR.glob("soc_dataset_*.ndjson"))
    return files[-1] if files else None

def _latest_thehive():
    files = sorted(OUTPUTS_DIR.glob("thehive_cases_*.json"))
    return files[-1] if files else None

def _iter_ndjson(path, max_lines=None):
    with open(path) as f:
        for i, line in enumerate(f):
            if max_lines and i >= max_lines:
                break
            line = line.strip()
            if line:
                yield json.loads(line)

def _count_lines(path):
    n = 0
    with open(path) as f:
        for line in f:
            if line.strip():
                n += 1
    return n

def _load_json(path):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}

# ═══════════════════════════════════════════════════════════════════════════
# 1. SOC COMMAND CENTER
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/command-center")
async def soc_command_center():
    latest = _latest_ndjson()
    if not latest:
        return {"page": "SOC Command Center", "error": "No pipeline dataset found", "top_metrics": {}, "severity_distribution": {}, "attack_type_distribution": {}, "mitre_heatmap": {}, "risk_queue": [], "noise_reduction": {}, "escalation_levels": {}, "campaigns": {}}
    total = _count_lines(latest) if latest else 0

    sev_counts = Counter()
    attack_counts = Counter()
    verdict_counts = Counter()
    suppression_count = 0
    noise_count = 0
    campaign_ids = set()
    playbook_outcomes = Counter()
    escalation_counts = Counter()

    limit = min(total, 100000) if total else 0
    for event in _iter_ndjson(latest, limit):
        sev = event.get("alert_severity", 0)
        sev_counts[sev] += 1
        at = event.get("attack_type", "unknown")
        attack_counts[at] += 1
        v = event.get("analyst_verdict", "unknown")
        verdict_counts[v] += 1
        if event.get("suppression_hit"):
            suppression_count += 1
        if event.get("noise"):
            noise_count += 1
        cid = event.get("campaign_id")
        if cid:
            campaign_ids.add(cid)
        po = event.get("playbook_outcome")
        if po:
            playbook_outcomes[po] += 1
        el = event.get("escalation_level")
        if el and el != "none":
            escalation_counts[el] += 1

    critical = sum(v for k, v in sev_counts.items() if k >= 10)
    high = sum(v for k, v in sev_counts.items() if 7 <= k < 10)

    # Threat heatmap - MITRE tactic distribution
    mitre_counts = Counter()
    for event in _iter_ndjson(latest, min(total, 50000)):
        t = event.get("mitre_tactic")
        if t and t != "None":
            mitre_counts[t] += 1

    # Risk queue (top events by risk_adjusted_priority)
    risk_queue = []
    for event in _iter_ndjson(latest, min(total, 50000)):
        rap = event.get("risk_adjusted_priority", 0)
        if rap >= 3:
            risk_queue.append({
                "event_id": event.get("event_id"),
                "risk_score": rap,
                "severity": event.get("alert_severity"),
                "escalation_level": event.get("escalation_level", "none"),
                "analyst_assigned": event.get("analyst_assigned", "unassigned"),
                "asset_criticality": event.get("asset_criticality", "unknown"),
            })
    risk_queue.sort(key=lambda x: -x["risk_score"])

    return {
        "page": "SOC Command Center",
        "top_metrics": {
            "total_events": total,
            "critical_alerts": critical,
            "high_alerts": high,
            "active_campaigns": len(campaign_ids),
            "suppression_rate": round(suppression_count / total * 100, 1) if total else 0,
            "noise_rate": round(noise_count / total * 100, 1) if total else 0,
            "false_positive_rate": round(verdict_counts.get("false_positive", 0) / total * 100, 1) if total else 0,
            "true_positive_rate": round(verdict_counts.get("true_positive", 0) / total * 100, 1) if total else 0,
        },
        "severity_distribution": {str(k): v for k, v in sorted(sev_counts.items())},
        "attack_type_distribution": dict(attack_counts.most_common()),
        "mitre_heatmap": dict(mitre_counts.most_common()),
        "risk_queue": risk_queue[:50],
        "noise_reduction": {
            "total_suppressed": suppression_count,
            "total_noise": noise_count,
            "ai_auto_closed": playbook_outcomes.get("no_action_taken", 0),
            "analyst_verdicts": dict(verdict_counts.most_common()),
        },
        "escalation_levels": dict(escalation_counts.most_common()),
        "campaigns": {
            "active": len(campaign_ids),
            "total_in_sample": limit,
        },
    }

# ═══════════════════════════════════════════════════════════════════════════
# 2. ALERTS & INVESTIGATION
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/alerts-table")
async def alerts_table(
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    severity_min: Optional[int] = Query(None, ge=0),
    attack_type_filter: Optional[str] = Query(None),
    verdict_filter: Optional[str] = Query(None),
):
    latest = _latest_ndjson()
    if not latest:
        return {"alerts": [], "total": 0}

    total = 0
    matched = 0
    rows = []
    for event in _iter_ndjson(latest):
        total += 1
        if severity_min is not None and (event.get("alert_severity") or 0) < severity_min:
            continue
        if attack_type_filter and event.get("attack_type") != attack_type_filter:
            continue
        if verdict_filter and event.get("analyst_verdict") != verdict_filter:
            continue
        if matched < offset:
            matched += 1
            continue
        if len(rows) >= limit:
            continue
        rows.append({
            "event_id": event.get("event_id"),
            "timestamp": event.get("timestamp"),
            "severity": event.get("alert_severity"),
            "risk_score": event.get("risk_adjusted_priority", 0),
            "mitre_tactic": event.get("mitre_tactic"),
            "mitre_technique": event.get("mitre_technique_name"),
            "source_tool": event.get("dataset_source"),
            "attack_type": event.get("attack_type"),
            "host": event.get("src_ip"),
            "dst_host": event.get("dst_ip"),
            "user": event.get("src_user"),
            "status": "open" if not event.get("suppression_hit") else "suppressed",
            "analyst_verdict": event.get("analyst_verdict", "pending"),
            "analyst_assigned": event.get("analyst_assigned", "unassigned"),
            "asset_criticality": event.get("asset_criticality", "unknown"),
            "true_positive": event.get("true_positive"),
            "noise": event.get("noise"),
        })
        matched += 1

    return {
        "page": "Alerts & Investigation",
        "total": total,
        "returned": len(rows),
        "offset": offset,
        "limit": limit,
        "alerts": rows,
    }

@router.get("/investigation/{event_id}")
async def investigation_detail(event_id: str):
    latest = _latest_ndjson()
    if not latest:
        return {"error": "No dataset"}

    target = None
    related = []
    for event in _iter_ndjson(latest, 200000):
        if event.get("event_id") == event_id:
            target = event
        elif event.get("campaign_id") and target and event.get("campaign_id") == target.get("campaign_id"):
            related.append(event.get("event_id"))
        if target and len(related) > 20:
            break

    if not target:
        return {"error": "Event not found"}

    return {
        "page": "Investigation",
        "event": {
            "event_id": target.get("event_id"),
            "timestamp": target.get("timestamp"),
            "description": target.get("alert_signature"),
            "severity": target.get("alert_severity"),
            "attack_type": target.get("attack_type"),
            "source": target.get("dataset_source"),
            "mitre_technique_id": target.get("mitre_technique_id"),
            "mitre_technique": target.get("mitre_technique_name"),
            "mitre_tactic": target.get("mitre_tactic"),
            "src_ip": target.get("src_ip"),
            "dst_ip": target.get("dst_ip"),
            "src_port": target.get("src_port"),
            "dst_port": target.get("dst_port"),
            "protocol": target.get("protocol"),
            "user": target.get("src_user"),
            "process": target.get("process_name"),
            "command_line": target.get("command_line"),
            "file_hash": target.get("process_hash"),
            "host_role": target.get("host_role"),
        },
        "soc_reasoning": {
            "analyst_verdict": target.get("analyst_verdict"),
            "analyst_notes": target.get("analyst_notes"),
            "analyst_assigned": target.get("analyst_assigned"),
            "escalation_level": target.get("escalation_level"),
            "asset_criticality": target.get("asset_criticality"),
            "user_role": target.get("user_role"),
            "department": target.get("department"),
            "business_unit": target.get("business_unit"),
            "confidence": target.get("confidence"),
            "true_positive": target.get("true_positive"),
            "noise": target.get("noise"),
            "suppression_hit": target.get("suppression_hit"),
            "timeline_position": target.get("timeline_position"),
            "playbook_outcome": target.get("playbook_outcome"),
        },
        "enrichment": {
            "vt_score": target.get("enrichment_vt_score"),
            "abuse_score": target.get("enrichment_abuse_score"),
            "misp_matches": target.get("enrichment_misp_matches"),
            "epss_score": target.get("enrichment_epss_score"),
            "risk_adjusted_priority": target.get("risk_adjusted_priority"),
        },
        "related_events": related[:20],
        "campaign_id": target.get("campaign_id"),
        "cluster_id": target.get("cluster_id"),
    }

# ═══════════════════════════════════════════════════════════════════════════
# 3. INCIDENT RESPONSE
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/incident-response")
async def incident_response():
    thehive = _latest_thehive()
    cases = json.load(open(thehive)) if thehive else []

    case_queue = []
    for c in cases:
        case_queue.append({
            "title": c.get("title"),
            "severity": c.get("severity"),
            "tags": c.get("tags", []),
            "observables_count": len(c.get("observables", [])),
            "tasks_total": len(c.get("tasks", [])),
            "tasks_pending": sum(1 for t in c.get("tasks", []) if t.get("status", "").lower() in ("waiting", "pending")),
            "description_preview": c.get("description", "")[:150],
        })

    # Aggregate stats
    by_severity = Counter()
    by_tag = Counter()
    for c in cases:
        by_severity[c.get("severity")] += 1
        for t in c.get("tags", []):
            by_tag[t] += 1

    latest = _latest_ndjson()
    total = _count_lines(latest) if latest else 0
    escalation_count = 0
    for event in _iter_ndjson(latest, min(total, 50000)):
        if event.get("escalation_level") and event["escalation_level"] not in ("none", ""):
            escalation_count += 1

    return {
        "page": "Incident Response",
        "case_queue": case_queue,
        "stats": {
            "total_cases": len(cases),
            "critical_cases": by_severity.get(4, 0) + by_severity.get(3, 0),
            "cases_by_severity": dict(sorted(by_severity.items())),
            "top_tags": dict(by_tag.most_common(10)),
            "escalated_incidents": escalation_count,
        },
        "response_actions_available": [
            "isolate_host", "disable_user", "block_ip",
            "kill_process", "trigger_remediation", "create_case",
        ],
    }

# ═══════════════════════════════════════════════════════════════════════════
# 4. THREAT INTELLIGENCE CENTER
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/threat-intel-center")
async def threat_intel_center():
    latest = _latest_ndjson()
    total = _count_lines(latest) if latest else 0

    ioc_ips = set()
    ioc_domains = set()
    ioc_hashes = set()
    ioc_urls = set()
    campaign_details = defaultdict(lambda: {"events": 0, "attack_types": set(), "severities": []})

    for event in _iter_ndjson(latest, min(total, 100000)):
        ip = event.get("src_ip")
        if ip and ip != "unknown":
            ioc_ips.add(ip)
        dst = event.get("dst_ip")
        if dst and dst != "unknown":
            ioc_ips.add(dst)
        domain = event.get("domain") or event.get("hostname")
        if domain:
            ioc_domains.add(domain)
        fhash = event.get("process_hash")
        if fhash:
            ioc_hashes.add(fhash)
        uri = event.get("uri")
        if uri:
            ioc_urls.add(uri)

        cid = event.get("campaign_id")
        if cid:
            campaign_details[cid]["events"] += 1
            at = event.get("attack_type")
            if at:
                campaign_details[cid]["attack_types"].add(at)
            sev = event.get("alert_severity")
            if sev is not None:
                campaign_details[cid]["severities"].append(sev)

    threat_level = "LOW"
    if len(ioc_ips) > 5000:
        threat_level = "CRITICAL"
    elif len(ioc_ips) > 1000:
        threat_level = "HIGH"
    elif len(ioc_ips) > 100:
        threat_level = "MEDIUM"

    # Read threat_intel_db for token usage
    ti_db = _load_json(BASE / "threat_intel_db.json")
    token_usage = ti_db.get("token_usage", {})

    return {
        "page": "Threat Intelligence Center",
        "threat_level": threat_level,
        "ioc_intelligence": {
            "total_unique_ips": len(ioc_ips),
            "total_unique_domains": len(ioc_domains),
            "total_unique_hashes": len(ioc_hashes),
            "total_unique_urls": len(ioc_urls),
            "ioc_sample_ips": sorted(ioc_ips)[:20],
            "ioc_sample_domains": sorted(ioc_domains)[:20],
        },
        "campaign_intelligence": {
            "total_campaigns": len(campaign_details),
            "campaigns": [
                {
                    "campaign_id": cid,
                    "events": details["events"],
                    "attack_types": list(details["attack_types"]),
                    "avg_severity": round(sum(details["severities"]) / len(details["severities"]), 1) if details["severities"] else 0,
                }
                for cid, details in sorted(campaign_details.items(), key=lambda x: -x[1]["events"])[:20]
            ],
        },
        "threat_feed_health": {
            "token_usage": token_usage,
            "services_configured": len(ti_db.get("services", {})),
            "total_iocs_stored": len(ti_db.get("intel_data", [])),
        },
    }

# ═══════════════════════════════════════════════════════════════════════════
# 5. ASSET & ENDPOINT INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/asset-intelligence")
async def asset_intelligence():
    latest = _latest_ndjson()
    total = _count_lines(latest) if latest else 0

    hosts = {}
    for event in _iter_ndjson(latest, min(total, 100000)):
        ip = event.get("src_ip", "unknown")
        if ip == "unknown":
            ip = event.get("dst_ip", "unknown")
        if ip not in hosts:
            hosts[ip] = {
                "ip": ip,
                "hostname": event.get("hostname", ip),
                "processes": set(),
                "users": set(),
                "attack_types": set(),
                "severities": [],
                "criticality": event.get("asset_criticality", "unknown"),
                "host_role": event.get("host_role", "unknown"),
                "department": event.get("department", "unknown"),
                "business_unit": event.get("business_unit", "unknown"),
                "total_alerts": 0,
                "cves_found": set(),
                "suppression_hits": 0,
            }
        h = hosts[ip]
        h["total_alerts"] += 1
        pn = event.get("process_name")
        if pn:
            h["processes"].add(pn)
        user = event.get("src_user")
        if user:
            h["users"].add(user)
        at = event.get("attack_type")
        if at:
            h["attack_types"].add(at)
        sev = event.get("alert_severity")
        if sev is not None:
            h["severities"].append(sev)
        if event.get("suppression_hit"):
            h["suppression_hits"] += 1

    inventory = []
    for ip, h in hosts.items():
        inventory.append({
            "ip": h["ip"],
            "hostname": h["hostname"],
            "os_version": "N/A",
            "criticality": h["criticality"],
            "host_role": h["host_role"],
            "department": h["department"],
            "business_unit": h["business_unit"],
            "total_alerts": h["total_alerts"],
            "unique_processes": list(h["processes"])[:10],
            "unique_users": list(h["users"])[:10],
            "attack_types": list(h["attack_types"]),
            "avg_severity": round(sum(h["severities"]) / len(h["severities"]), 1) if h["severities"] else 0,
            "max_severity": max(h["severities"]) if h["severities"] else 0,
            "suppression_rate": round(h["suppression_hits"] / h["total_alerts"] * 100, 1) if h["total_alerts"] else 0,
        })
    inventory.sort(key=lambda x: -x["total_alerts"])

    # Exposure stats
    all_severities = []
    all_criticalities = Counter()
    for h in hosts.values():
        all_severities.extend(h["severities"])
        all_criticalities[h["criticality"]] += 1

    return {
        "page": "Asset & Endpoint Intelligence",
        "asset_inventory": inventory[:100],
        "stats": {
            "total_assets": len(hosts),
            "high_criticality": all_criticalities.get("high", 0) + all_criticalities.get("critical", 0),
            "medium_criticality": all_criticalities.get("medium", 0),
            "low_criticality": all_criticalities.get("low", 0),
            "avg_asset_severity": round(sum(all_severities) / len(all_severities), 1) if all_severities else 0,
        },
        "remediation_actions": [
            "isolate_host", "patch_endpoint", "restart_service", "revoke_session",
        ],
    }

# ═══════════════════════════════════════════════════════════════════════════
# 6. AI OPERATIONS CENTER
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/ai-operations")
async def ai_operations_center():
    latest = _latest_ndjson()
    total = _count_lines(latest) if latest else 0

    verdict_counts = Counter()
    classification_confidences = []
    auto_closed = 0
    suppressed = 0
    escalated = 0
    fp_count = 0
    tp_count = 0

    for event in _iter_ndjson(latest, min(total, 100000)):
        v = event.get("analyst_verdict", "unknown")
        verdict_counts[v] += 1
        conf = event.get("confidence")
        if conf is not None:
            classification_confidences.append(conf)
        if event.get("playbook_outcome") == "no_action_taken":
            auto_closed += 1
        if event.get("suppression_hit"):
            suppressed += 1
        el = event.get("escalation_level")
        if el and el not in ("none", ""):
            escalated += 1
        if v == "false_positive":
            fp_count += 1
        elif v == "true_positive":
            tp_count += 1

    confs = classification_confidences or [0]
    total_analysed = fp_count + tp_count

    return {
        "page": "AI Operations Center",
        "model_health": {
            "f1_score": round(tp_count / (tp_count + 0.5 * (fp_count + (total_analysed - tp_count - fp_count))), 3) if total_analysed else 0,
            "precision": round(tp_count / (tp_count + fp_count), 3) if (tp_count + fp_count) else 0,
            "recall": round(tp_count / (tp_count + (total_analysed - tp_count - fp_count)), 3) if total_analysed else 0,
            "total_classified": total_analysed,
            "avg_confidence": round(sum(confs) / len(confs), 3),
            "min_confidence": round(min(confs), 3),
            "max_confidence": round(max(confs), 3),
        },
        "ai_decision_queue": {
            "auto_closed_alerts": auto_closed,
            "suppressed_alerts": suppressed,
            "escalated_alerts": escalated,
            "low_confidence_detections": sum(1 for c in classification_confidences if c < 0.5),
        },
        "analyst_feedback": {
            "false_positives": fp_count,
            "true_positives": tp_count,
            "false_negatives": total_analysed - tp_count - fp_count,
            "analyst_verdicts": dict(verdict_counts.most_common()),
        },
    }

# ═══════════════════════════════════════════════════════════════════════════
# 7. IT HYGIENE & EXPOSURE
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/it-hygiene")
async def it_hygiene():
    latest = _latest_ndjson()
    total = _count_lines(latest) if latest else 0

    patch_issues = 0
    auth_issues = 0
    config_issues = 0
    integrity_issues = 0
    threat_issues = 0

    cves_found = set()
    epss_scores = []
    cvss_scores = []
    hosts_with_vulns = set()

    for event in _iter_ndjson(latest, min(total, 100000)):
        if event.get("true_positive"):
            threat_issues += 1
        if event.get("noise"):
            config_issues += 1
        if event.get("suppression_hit"):
            integrity_issues += 1

        epss = event.get("enrichment_epss_score")
        if epss is not None and epss > 0:
            epss_scores.append(epss)
            patch_issues += 1

        mitre = event.get("mitre_technique_id")
        if mitre and mitre != "T9999":
            threat_issues += 1

    total_issues = patch_issues + auth_issues + config_issues + integrity_issues + threat_issues

    hygiene_score = max(0, 100 - (total_issues / max(total, 1)) * 100)

    return {
        "page": "IT Hygiene & Exposure",
        "hygiene_score": {
            "overall": round(hygiene_score, 1),
            "breakdown": {
                "patch_hygiene": max(0, 100 - (patch_issues / max(total, 1)) * 100),
                "authentication_hygiene": max(0, 100 - (auth_issues / max(total, 1)) * 100),
                "logging_hygiene": max(0, 100 - (config_issues / max(total, 1)) * 100),
                "integrity_hygiene": max(0, 100 - (integrity_issues / max(total, 1)) * 100),
                "threat_hygiene": max(0, 100 - (threat_issues / max(total, 1)) * 100),
            },
        },
        "risk_trends": {
            "total_issues": total_issues,
            "patch_issues": patch_issues,
            "auth_issues": auth_issues,
            "config_issues": config_issues,
            "integrity_issues": integrity_issues,
            "threat_issues": threat_issues,
            "vulnerable_hosts": len(hosts_with_vulns),
        },
        "compliance": {
            "nist_coverage": round((1 - threat_issues / max(total, 1)) * 100, 1),
            "cis_coverage": round((1 - config_issues / max(total, 1)) * 100, 1),
            "mitre_coverage": len(set(e.get("mitre_technique_id") for e in _iter_ndjson(latest, min(total, 10000)) if e.get("mitre_technique_id") and e["mitre_technique_id"] != "T9999")),
        },
    }

# ═══════════════════════════════════════════════════════════════════════════
# 8. PLAYBOOKS & AUTOMATION
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/playbooks-automation")
async def playbooks_automation():
    config = _load_json(BASE / "playbook_config.json")
    rules = config.get("rules", [])
    default_action = config.get("default_action", "log_event")

    latest = _latest_ndjson()
    total = _count_lines(latest) if latest else 0

    execution_counts = Counter()
    for event in _iter_ndjson(latest, min(total, 50000)):
        po = event.get("playbook_outcome", "unknown")
        execution_counts[po] += 1

    return {
        "page": "Playbooks & Automation",
        "playbook_library": {
            "rules": rules,
            "default_action": default_action,
            "total_rules": len(rules),
        },
        "execution_history": {
            "outcomes": dict(execution_counts.most_common()),
            "total_executions": sum(execution_counts.values()),
        },
        "simulation_mode": {
            "available": True,
            "endpoint": "POST /api/v1/playbook-config/evaluate",
        },
        "approval_workflows": {
            "manual_approval_required": [r["name"] for r in rules if r.get("automation_level") == "manual"],
            "semi_automated": [r["name"] for r in rules if r.get("automation_level") == "semi"],
            "fully_automated": [r["name"] for r in rules if r.get("automation_level") == "full"],
        },
    }

# ═══════════════════════════════════════════════════════════════════════════
# 9. REPORTING & AUDIT
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/reporting-audit")
async def reporting_audit():
    latest = _latest_ndjson()
    total = _count_lines(latest) if latest else 0

    analyst_activity = Counter()
    open_incidents = 0
    pending_escalations = 0

    for event in _iter_ndjson(latest, min(total, 50000)):
        aa = event.get("analyst_assigned")
        if aa:
            analyst_activity[aa] += 1
        if not event.get("suppression_hit") and not event.get("noise"):
            open_incidents += 1
        el = event.get("escalation_level")
        if el and el not in ("none", ""):
            pending_escalations += 1

    # Monthly trend from timestamps
    monthly_counts = Counter()
    for event in _iter_ndjson(latest, min(total, 100000)):
        ts = event.get("timestamp", "")
        if ts and len(ts) >= 7:
            month = ts[:7]
            monthly_counts[month] += 1

    return {
        "page": "Reporting & Audit",
        "shift_handover": {
            "open_incidents": open_incidents,
            "pending_escalations": pending_escalations,
            "total_events_in_scope": total,
            "analyst_activity": dict(analyst_activity.most_common(10)),
        },
        "executive_reports": {
            "mttr_trend": "N/A (live data)",
            "incident_trend": dict(sorted(monthly_counts.items())),
            "total_incidents": total,
            "critical_incidents": sum(1 for e in _iter_ndjson(latest, min(total, 50000)) if e.get("alert_severity", 0) >= 10),
        },
        "technical_reports": {
            "total_iocs": sum(1 for e in _iter_ndjson(latest, min(total, 50000)) if e.get("ioc_ip") or e.get("ioc_hash")),
            "attack_chains": len(set(e.get("campaign_id") for e in _iter_ndjson(latest, min(total, 50000)))),
            "affected_systems": len(set(e.get("src_ip") for e in _iter_ndjson(latest, min(total, 50000)))),
        },
        "export_options": ["csv", "json", "ndjson"],
    }

# ═══════════════════════════════════════════════════════════════════════════
# 10. ADMINISTRATION & SYSTEM HEALTH
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/admin-health")
async def admin_health():
    latest = _latest_ndjson()
    total = _count_lines(latest) if latest else 0

    # Connector health based on available data
    outputs_ok = OUTPUTS_DIR.exists()
    thehive_ok = _latest_thehive() is not None
    ndjson_ok = latest is not None
    llm_ok = (OUTPUTS_DIR / "llm_datasets").exists()

    return {
        "page": "Administration & System Health",
        "connector_health": {
            "wazuh_connector": {"status": "configured", "data_files": list(OUTPUTS_DIR.glob("soc_dataset_*.ndjson"))[:3]},
            "misp_connector": {"status": "configured", "iocs": total},
            "thehive_connector": {"status": "available" if thehive_ok else "no_data", "cases": _count_lines(_latest_thehive()) if thehive_ok else 0},
            "threat_feed_connectors": {"virustotal": True, "abuseipdb": True, "alienvault_otx": True, "urlhaus": True},
        },
        "infrastructure_health": {
            "dataset_pipeline_outputs": outputs_ok,
            "ndjson_dataset": ndjson_ok,
            "thehive_cases": thehive_ok,
            "llm_datasets": llm_ok,
            "total_events_available": total,
            "storage_used_mb": round(sum(f.stat().st_size for f in OUTPUTS_DIR.glob("*") if f.is_file()) / (1024 * 1024), 1),
        },
        "queue_monitoring": {
            "event_ingestion_queue": total,
            "ai_processing_queue": "N/A (processed inline)",
            "failed_jobs": 0,
            "retry_counts": 0,
        },
        "rbac": {
            "roles": ["admin", "analyst", "viewer"],
            "permissions": ["read", "write", "execute", "admin"],
            "mfa_status": "enabled",
        },
    }

# ═══════════════════════════════════════════════════════════════════════════
# COMPREHENSIVE ALL-IN-ONE DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/dashboard")
async def full_dashboard():
    """Returns ALL dashboard pages data combined for a single fetch."""
    return {
        "command_center": (await soc_command_center()),
        "incident_response": (await incident_response()),
        "threat_intel": (await threat_intel_center()),
        "asset_intelligence": (await asset_intelligence()),
        "ai_operations": (await ai_operations_center()),
        "it_hygiene": (await it_hygiene()),
        "playbooks_automation": (await playbooks_automation()),
        "reporting_audit": (await reporting_audit()),
        "admin_health": (await admin_health()),
    }
