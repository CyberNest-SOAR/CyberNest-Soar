import asyncio
import logging
from fastapi import APIRouter
from typing import List
from schemas.models import RiskScoreRequest, RiskScoreResponse, UnifiedAlert
from services.risk import calculate_risk_score

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk-score", tags=["Team 1: Risk Scoring"])

@router.post("/", response_model=RiskScoreResponse)
async def risk_score(request: RiskScoreRequest):
    alert = request.alert
    
    result = await calculate_risk_score(alert)
    
    return RiskScoreResponse(
        event_id=alert.event_id,
        risk_score=result["risk_score"],
        priority=result["priority"],
        predicted_analyst_verdict=result["predicted_analyst_verdict"],
        confidence=result["confidence"],
        features=result["features"]
    )


@router.post("/batch", response_model=List[RiskScoreResponse])
async def risk_score_batch(alerts: List[UnifiedAlert]):
    """
    Score a batch of alerts. Accepts the raw ``List[UnifiedAlert]``
    array returned by ``GET /alerts/``.
    """
    results = await asyncio.gather(
        *[calculate_risk_score(a) for a in alerts],
        return_exceptions=True,
    )
    out = []
    for alert, result in zip(alerts, results):
        if isinstance(result, Exception):
            logger.warning("[Risk] Scoring failed for %s: %s", alert.event_id, result)
            continue
        out.append(RiskScoreResponse(
            event_id=alert.event_id,
            risk_score=result["risk_score"],
            priority=result["priority"],
            predicted_analyst_verdict=result["predicted_analyst_verdict"],
            confidence=result["confidence"],
            features=result["features"],
        ))
    return out
