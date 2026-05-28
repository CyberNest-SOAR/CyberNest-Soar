import logging
from fastapi import APIRouter, Body
from typing import List
from schemas.models import UnifiedAlert, RiskScoreResponse, PatchResponse, FilterResult, PlaybookDecisionResponse, PlaybookDecisionRequest
from services.risk import calculate_risk_score
from services.patch import get_patch_recommendations
from services.filtering import classify_alert
from routers.filtering import prepare_llm_payload
from services.playbooks import get_playbook_decision

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-analysis", tags=["AI Analysis"])

@router.post("/llm/classify")
async def llm_classify(alert: UnifiedAlert):
    payload = prepare_llm_payload(alert)
    result = await classify_alert(payload)
    return {
        "engine": "llm",
        "classification": result["classification"],
        "confidence": result["confidence"],
        "features": payload,
    }

@router.post("/scoring")
async def scoring_ai(alert: UnifiedAlert):
    result = await calculate_risk_score(alert)
    return {
        "engine": "scoring_ai",
        "risk_score": result["risk_score"],
        "priority": result["priority"],
        "confidence": result["confidence"],
        "features": result["features"],
    }

@router.post("/patching")
async def patching_ai(alert: UnifiedAlert):
    result = await get_patch_recommendations(alert)
    return {
        "engine": "patching_ai",
        "host": result.host,
        "recommendations": [r.model_dump() for r in result.recommendations],
    }

@router.post("/playbook-analysis")
async def playbook_analysis(alert: UnifiedAlert):
    decision = await get_playbook_decision(alert)
    return {
        "engine": "playbook_analysis",
        "action": decision["action"],
        "confidence": decision["confidence"],
        "automation_level": decision["automation_level"],
        "reason": decision["reason"],
    }

@router.post("/full-analysis")
async def full_ai_analysis(alert: UnifiedAlert):
    risk = await calculate_risk_score(alert)
    patch = await get_patch_recommendations(alert)
    payload = prepare_llm_payload(alert)
    llm_result = await classify_alert(payload)
    playbook = await get_playbook_decision(alert)

    return {
        "event_id": alert.event_id,
        "analyses": {
            "llm": {
                "classification": llm_result["classification"],
                "confidence": llm_result["confidence"],
            },
            "scoring_ai": {
                "risk_score": risk["risk_score"],
                "priority": risk["priority"],
            },
            "patching_ai": {
                "recommendations": [r.model_dump() for r in patch.recommendations],
            },
            "playbook_analysis": {
                "action": playbook["action"],
                "automation_level": playbook["automation_level"],
            },
        },
    }
