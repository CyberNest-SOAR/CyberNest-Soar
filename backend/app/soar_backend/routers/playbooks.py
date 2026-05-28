from fastapi import APIRouter
from schemas.models import PlaybookDecisionRequest, PlaybookDecisionResponse, CaseCreate, UnifiedAlert
from services.playbooks import get_playbook_decision
from collectors.thehive_client import create_case

router = APIRouter(prefix="/playbooks", tags=["Team 4: Playbooks"])

@router.post("/decision", response_model=PlaybookDecisionResponse)
async def get_decision(request: PlaybookDecisionRequest):
    """
    Unified Decision Engine: Combines tag-based logic with risk-score thresholds.
    """
    alert = request.alert
    decision = await get_playbook_decision(alert)

    return PlaybookDecisionResponse(
        action=decision["action"],
        confidence=decision["confidence"],
        automation_level=decision["automation_level"],
        reason=decision["reason"]
    )

@router.post("/create-case")
async def create_case_endpoint(case: CaseCreate):
    """
    Create a TheHive case with pipeline-compatible rich format.
    Accepts alert data and generates a full case with observables and tasks.
    """
    soc = getattr(case, "soc_reasoning", None) or {}
    if hasattr(soc, "model_dump"):
        soc = soc.model_dump()

    result = create_case(
        title=case.title,
        severity=case.severity,
        description=case.description,
        tags=case.tags,
        source_ip=case.source_ip,
        destination_ip=case.destination_ip,
        attack_type=case.attack_type,
        mitre_tactic=case.mitre_tactic,
    )
    return result

@router.post("/from-alert")
async def create_case_from_alert(alert: UnifiedAlert):
    """
    Create a TheHive case directly from a UnifiedAlert.
    Extracts all relevant fields from the alert automatically.
    """
    severity = alert.severity
    if severity >= 10:
        hive_severity = 4
    elif severity >= 7:
        hive_severity = 3
    elif severity >= 4:
        hive_severity = 2
    else:
        hive_severity = 1

    soc = alert.soc_reasoning or {}
    attack_type = getattr(soc, "attack_type", None) or ""
    mitre_tactic = getattr(soc, "mitre_tactic", None) or ""
    source_ip = alert.host_context.ip_address

    title = f"[{'HIGH' if hive_severity >= 3 else 'MEDIUM' if hive_severity >= 2 else 'LOW'}] {alert.description[:80]}"

    result = create_case(
        title=title,
        severity=hive_severity,
        description=alert.description,
        tags=[alert.source, attack_type, mitre_tactic] if attack_type else [alert.source],
        source_ip=source_ip,
        destination_ip="",
        attack_type=attack_type,
        mitre_tactic=mitre_tactic,
    )
    return result
