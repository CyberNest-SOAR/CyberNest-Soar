from fastapi import APIRouter
from schemas.models import PlaybookDecisionRequest, PlaybookDecisionResponse
from services.playbooks import get_playbook_decision

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