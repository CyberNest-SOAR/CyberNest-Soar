from fastapi import APIRouter
from schemas.models import RiskScoreRequest, RiskScoreResponse
from services.risk import calculate_risk_score

router = APIRouter(prefix="/risk-score", tags=["Team 1: Risk Scoring"])

@router.post("/", response_model=RiskScoreResponse)
async def risk_score(request: RiskScoreRequest):
    alert = request.alert
    
    result = await calculate_risk_score(alert)
    
    return RiskScoreResponse(
        event_id=alert.event_id,
        risk_score=result["risk_score"],
        priority=result["priority"],
        confidence=result["confidence"],
        features=result["features"]
    )
